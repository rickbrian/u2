from __future__ import absolute_import, print_function

import logging
import re
import time
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple, Union

import adbutils

from uiautomator2._proto import HTTP_TIMEOUT, SCROLL_STEPS, Direction
from uiautomator2.abstract import ShellResponse
from uiautomator2.core import BasicUiautomatorServer, WiFiUiautomatorServer, WiFiUiautomatorServer
from uiautomator2.exceptions import *
from uiautomator2.settings import Settings
from uiautomator2.utils import deprecated, image_convert, list2cmdline

logger = logging.getLogger(__name__)


class _WiFiBaseClient(WiFiUiautomatorServer):
    """
    WiFi mode base client (no ADB required)
    """
    def __init__(self, host: str, port: int = 9008):
        self.__host = host
        self.__port = port
        self._dev = None  # No ADB device in WiFi mode
        self._debug = False
        WiFiUiautomatorServer.__init__(self, host, port)
    
    @property
    def _serial(self) -> str:
        return f"{self.__host}:{self.__port}"
    
    @property
    def adb_device(self) -> Optional[adbutils.AdbDevice]:
        """WiFi mode: no ADB device"""
        return None
    
    @cached_property
    def settings(self) -> Settings:
        return Settings(self)

    def sleep(self, seconds: float):
        """ same as time.sleep """
        time.sleep(seconds)

    def shell(self, cmdargs: Union[str, List[str]], timeout=60) -> ShellResponse:
        """
        Run shell command on device using superShell JSON-RPC method (requires root)

        Args:
            cmdargs: str or list, example: "ls -l" or ["ls", "-l"]
            timeout: seconds of command run

        Returns:
            ShellResponse

        Raises:
            AdbShellError
        """
        try:
            if self.debug:
                print("shell:", list2cmdline(cmdargs))
            logger.debug("shell: %s", list2cmdline(cmdargs))
            
            # Convert cmdargs to string if it's a list
            if isinstance(cmdargs, list):
                cmd_str = list2cmdline(cmdargs)
            else:
                cmd_str = cmdargs
            
            # Use superShell JSON-RPC method
            result = self.jsonrpc.superShell(cmd_str)
            # superShell returns string output, assume success (exit code 0)
            return ShellResponse(result, 0)
        except Exception as e:
            logger.error(f"superShell failed: {e}")
            raise AdbShellError(f"superShell failed: {e}")
    
    @property
    def device_info(self) -> Dict[str, Any]:
        """Get device info via JSON-RPC"""
        info = self.jsonrpc.deviceInfo()
        return {
            "serial": f"{self.__host}:{self.__port}",
            "sdk": info.get('sdkInt'),
            "brand": info.get('productName', '').split('_')[0] if '_' in info.get('productName', '') else '',
            "model": info.get('productName', ''),
            "arch": None,  # Not available via JSON-RPC
            "version": info.get('sdkInt'),
        }
    
    @property
    def wlan_ip(self) -> Optional[str]:
        """WiFi mode: return the host IP"""
        return self.__host

    @property
    def info(self) -> Dict[str, Any]:
        """Get device info via JSON-RPC"""
        return self.jsonrpc.deviceInfo(http_timeout=10)

    @property
    def jsonrpc(self):
        class JSONRpcWrapper():
            def __init__(self, server: WiFiUiautomatorServer):
                self.server = server
                self.method = None

            def __getattr__(self, method):
                self.method = method  # jsonrpc function name
                return self

            def __call__(self, *args, **kwargs):
                http_timeout = kwargs.pop('http_timeout', HTTP_TIMEOUT)
                params = args if args else kwargs
                return self.server.jsonrpc_call(self.method, params, http_timeout)

        return JSONRpcWrapper(self)


class _BaseClient(BasicUiautomatorServer):
    """
    提供最基础的控制类，这个类暂时先不公开吧
    """

    def __init__(self, serial: Optional[Union[str, adbutils.AdbDevice]] = None):
        """
        Args:
            serial: device serialno
        """
        if isinstance(serial, adbutils.AdbDevice):
            self.__serial = serial.serial
            self._dev = serial
        else:
            self.__serial = serial
            self._dev = self._wait_for_device()
        self._debug = False
        BasicUiautomatorServer.__init__(self, self._dev)
    
    @property
    def _serial(self) -> str:
        return self.__serial
    
    def _wait_for_device(self, timeout=10) -> adbutils.AdbDevice:
        """
        wait for device came online, if device is remote, reconnect every 1s

        Returns:
            adbutils.AdbDevice
        
        Raises:
            ConnectError
        """
        for d in adbutils.adb.device_list():
            if d.serial == self._serial:
                return d

        _RE_remote_adb = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$")
        _is_remote = _RE_remote_adb.match(self._serial) is not None

        adb = adbutils.adb
        deadline = time.time() + timeout
        while time.time() < deadline:
            title = "device reconnecting" if _is_remote else "wait-for-device"
            logger.debug("%s, time left(%.1fs)", title, deadline - time.time())
            if _is_remote:
                try:
                    adb.disconnect(self._serial)
                    adb.connect(self._serial, timeout=1)
                except (adbutils.AdbError, adbutils.AdbTimeout) as e:
                    logger.debug("adb reconnect error: %s", str(e))
                    time.sleep(1.0)
                    continue
            try:
                adb.wait_for(self._serial, timeout=1)
            except (adbutils.AdbError, adbutils.AdbTimeout):
                continue
            return adb.device(self._serial)
        raise ConnectError(f"device {self._serial} not online")

    @property
    def adb_device(self) -> Optional[adbutils.AdbDevice]:
        """Return ADB device if available, None for WiFi mode"""
        return getattr(self, '_dev', None)
    
    @cached_property
    def settings(self) -> Settings:
        return Settings(self)

    def sleep(self, seconds: float):
        """ same as time.sleep """
        time.sleep(seconds)

    def shell(self, cmdargs: Union[str, List[str]], timeout=60) -> ShellResponse:
        """
        Run shell command on device
        In WiFi mode, uses superShell JSON-RPC method (requires root)
        In ADB mode, uses ADB shell

        Args:
            cmdargs: str or list, example: "ls -l" or ["ls", "-l"]
            timeout: seconds of command run, works on when stream is False

        Returns:
            ShellResponse

        Raises:
            AdbShellError
        """
        try:
            if self.debug:
                print("shell:", list2cmdline(cmdargs))
            logger.debug("shell: %s", list2cmdline(cmdargs))
            
            # Convert cmdargs to string if it's a list
            if isinstance(cmdargs, list):
                cmd_str = list2cmdline(cmdargs)
            else:
                cmd_str = cmdargs
            
            # Check if we're in WiFi mode (no ADB device)
            is_wifi_mode = not hasattr(self, '_dev') or self._dev is None
            
            # Try superShell JSON-RPC method first (for WiFi mode or root commands)
            try:
                result = self.jsonrpc.superShell(cmd_str)
                # superShell returns string output, assume success (exit code 0)
                return ShellResponse(result, 0)
            except (AttributeError, KeyError, Exception) as e:
                # If superShell is not available
                if is_wifi_mode:
                    # WiFi mode: superShell is required, cannot fall back to ADB
                    logger.error("superShell failed in WiFi mode: %s", e)
                    raise AdbShellError(f"superShell failed in WiFi mode: {e}")
                else:
                    # ADB mode: fall back to ADB shell
                    logger.debug("superShell not available, falling back to ADB shell: %s", e)
                    if hasattr(self, '_dev') and self._dev:
                        ret = self._dev.shell2(cmdargs, timeout=timeout)
                        return ShellResponse(ret.output, ret.returncode)
                    else:
                        raise AdbShellError("Neither superShell nor ADB shell available")
        except adbutils.AdbError as e:
            raise AdbShellError(e)

    @property
    def info(self) -> Dict[str, Any]:
        return self.jsonrpc.deviceInfo(http_timeout=10)
    
    @property
    def device_info(self) -> Dict[str, Any]:
        if self._dev is None:
            # WiFi mode: get info via JSON-RPC
            info = self.jsonrpc.deviceInfo()
            return {
                "serial": "wifi_mode",
                "sdk": info.get('sdkInt'),
                "brand": info.get('productName', '').split('_')[0] if '_' in info.get('productName', '') else '',
                "model": info.get('productName', ''),
                "arch": None,
                "version": info.get('sdkInt'),
            }
        serial = self._dev.getprop("ro.serialno")
        sdk = self._dev.getprop("ro.build.version.sdk")
        version = self._dev.getprop("ro.build.version.release")
        brand = self._dev.getprop("ro.product.brand")
        model = self._dev.getprop("ro.product.model")
        arch = self._dev.getprop("ro.product.cpu.abi")
        return {
            "serial": serial,
            "sdk": int(sdk) if sdk.isdigit() else None,
            "brand": brand,
            "model": model,
            "arch": arch,
            "version": int(version) if version.isdigit() else None,
        }

    @property
    def wlan_ip(self) -> Optional[str]:
        if self._dev is None:
            return None  # WiFi mode: IP is already known
        try:
            return self._dev.wlan_ip()
        except adbutils.AdbError:
            return None

    @property
    def jsonrpc(self):
        class JSONRpcWrapper():
            def __init__(self, server: BasicUiautomatorServer):
                self.server = server
                self.method = None

            def __getattr__(self, method):
                self.method = method  # jsonrpc function name
                return self

            def __call__(self, *args, **kwargs):
                http_timeout = kwargs.pop('http_timeout', HTTP_TIMEOUT)
                params = args if args else kwargs
                return self.server.jsonrpc_call(self.method, params, http_timeout)

        return JSONRpcWrapper(self)

    def reset_uiautomator(self):
        """
        restart uiautomator service

        Orders:
            - stop uiautomator keeper
            - am force-stop com.github.uiautomator
            - start uiautomator keeper(am instrument -w ...)
            - wait until uiautomator service is ready
        
        Note:
            WiFi mode: Server should be managed externally, this method only checks connectivity
        """
        # WiFi mode: just check if server is alive
        if not hasattr(self, '_dev') or self._dev is None:
            self.start_uiautomator()  # This will check if server is alive
            return
        
        # ADB mode: restart uiautomator
        self.stop_uiautomator()
        self.start_uiautomator()

    def push(self, src, dst: str, mode=0o644):
        """
        Push file into device

        Args:
            src (path or fileobj): source file
            dst (str): destination can be folder or file path
            mode (int): file mode
        
        Note:
            WiFi mode: Not supported, requires ADB for file transfer
        """
        if not hasattr(self, '_dev') or self._dev is None:
            raise DeviceError("push is not supported in WiFi mode. Use ADB mode or manually transfer files.")
        self._dev.sync.push(src, dst, mode=mode)

    def pull(self, src: str, dst: str):
        """
        Pull file from device to local
        
        Note:
            WiFi mode: Not supported, requires ADB for file transfer
        """
        if not hasattr(self, '_dev') or self._dev is None:
            raise DeviceError("pull is not supported in WiFi mode. Use ADB mode or manually transfer files.")
        try:
            self._dev.sync.pull(src, dst, exist_ok=True)
        except TypeError:
            self._dev.sync.pull(src, dst)

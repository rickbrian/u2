#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 WiFi 模式下所有接口的可用性
"""

import sys
import os
import traceback

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uiautomator2 as u2


def test_interface(name, func, *args, **kwargs):
    """测试接口是否可用"""
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        return False, None, str(e)


def main():
    device_address = "192.168.25.22:9008"
    
    print("=" * 60)
    print("WiFi 模式接口可用性测试")
    print("=" * 60)
    print(f"\n正在连接设备: {device_address}")
    
    try:
        d = u2.connect_wifi(device_address)
        print("[OK] 连接成功！\n")
    except Exception as e:
        print(f"[FAIL] 连接失败: {e}")
        return
    
    results = {
        "可用": [],
        "不可用": [],
        "部分可用": []
    }
    
    # ========== 基础信息接口 ==========
    print("\n【基础信息接口】")
    print("-" * 60)
    
    # info
    success, result, error = test_interface("info", lambda: d.info)
    if success:
        print(f"[OK] info: {result.get('displayWidth', 'N/A')}x{result.get('displayHeight', 'N/A')}")
        results["可用"].append("info")
    else:
        print(f"[FAIL] info: {error}")
        results["不可用"].append("info")
    
    # device_info
    success, result, error = test_interface("device_info", lambda: d.device_info)
    if success:
        print(f"[OK] device_info: {result}")
        results["可用"].append("device_info")
    else:
        print(f"[FAIL] device_info: {error}")
        results["不可用"].append("device_info")
    
    # wlan_ip
    success, result, error = test_interface("wlan_ip", lambda: d.wlan_ip)
    if success:
        print(f"[OK] wlan_ip: {result}")
        results["可用"].append("wlan_ip")
    else:
        print(f"[FAIL] wlan_ip: {error}")
        results["不可用"].append("wlan_ip")
    
    # window_size
    success, result, error = test_interface("window_size", lambda: d.window_size())
    if success:
        print(f"[OK] window_size: {result}")
        results["可用"].append("window_size")
    else:
        print(f"[FAIL] window_size: {error}")
        results["不可用"].append("window_size")
    
    # ========== 截图接口 ==========
    print("\n【截图接口】")
    print("-" * 60)
    
    # screenshot
    success, result, error = test_interface("screenshot", lambda: d.screenshot(format='opencv'))
    if success and result is not None:
        print(f"[OK] screenshot: {result.shape if hasattr(result, 'shape') else 'OK'}")
        results["可用"].append("screenshot")
    else:
        print(f"[FAIL] screenshot: {error}")
        results["不可用"].append("screenshot")
    
    # takeScreenshot (JSON-RPC)
    try:
        result = d.jsonrpc.takeScreenshot(1, 80)
        if result:
            print(f"[OK] jsonrpc.takeScreenshot: OK (返回 {len(result)} 字符)")
            results["可用"].append("jsonrpc.takeScreenshot")
        else:
            print(f"[WARN] jsonrpc.takeScreenshot: 返回 None")
            results["部分可用"].append("jsonrpc.takeScreenshot")
    except Exception as e:
        print(f"[FAIL] jsonrpc.takeScreenshot: {e}")
        results["不可用"].append("jsonrpc.takeScreenshot")
    
    # ========== UI 操作接口 ==========
    print("\n【UI 操作接口】")
    print("-" * 60)
    
    # click
    try:
        # 只测试接口是否存在，不实际点击
        if hasattr(d, 'click'):
            print("[OK] click: 接口存在")
            results["可用"].append("click")
        else:
            print("[FAIL] click: 接口不存在")
            results["不可用"].append("click")
    except Exception as e:
        print(f"[FAIL] click: {e}")
        results["不可用"].append("click")
    
    # swipe
    try:
        if hasattr(d, 'swipe'):
            print("[OK] swipe: 接口存在")
            results["可用"].append("swipe")
        else:
            print("[FAIL] swipe: 接口不存在")
            results["不可用"].append("swipe")
    except Exception as e:
        print(f"[FAIL] swipe: {e}")
        results["不可用"].append("swipe")
    
    # press
    try:
        if hasattr(d, 'press'):
            print("[OK] press: 接口存在")
            results["可用"].append("press")
        else:
            print("[FAIL] press: 接口不存在")
            results["不可用"].append("press")
    except Exception as e:
        print(f"[FAIL] press: {e}")
        results["不可用"].append("press")
    
    # long_click
    try:
        if hasattr(d, 'long_click'):
            print("[OK] long_click: 接口存在")
            results["可用"].append("long_click")
        else:
            print("[FAIL] long_click: 接口不存在")
            results["不可用"].append("long_click")
    except Exception as e:
        print(f"[FAIL] long_click: {e}")
        results["不可用"].append("long_click")
    
    # double_click
    try:
        if hasattr(d, 'double_click'):
            print("[OK] double_click: 接口存在")
            results["可用"].append("double_click")
        else:
            print("[FAIL] double_click: 接口不存在")
            results["不可用"].append("double_click")
    except Exception as e:
        print(f"[FAIL] double_click: {e}")
        results["不可用"].append("double_click")
    
    # ========== 文本输入接口 ==========
    print("\n【文本输入接口】")
    print("-" * 60)
    
    # send_keys
    try:
        if hasattr(d, 'send_keys'):
            print("[OK] send_keys: 接口存在")
            results["可用"].append("send_keys")
        else:
            print("[FAIL] send_keys: 接口不存在")
            results["不可用"].append("send_keys")
    except Exception as e:
        print(f"[FAIL] send_keys: {e}")
        results["不可用"].append("send_keys")
    
    # clear_text
    try:
        if hasattr(d, 'clear_text'):
            print("[OK] clear_text: 接口存在")
            results["可用"].append("clear_text")
        else:
            print("[FAIL] clear_text: 接口不存在")
            results["不可用"].append("clear_text")
    except Exception as e:
        print(f"[FAIL] clear_text: {e}")
        results["不可用"].append("clear_text")
    
    # ========== Shell 接口 ==========
    print("\n【Shell 接口】")
    print("-" * 60)
    
    # shell (需要 root)
    success, result, error = test_interface("shell", lambda: d.shell("echo test"))
    if success:
        print(f"[OK] shell: {result.output[:50] if result else 'OK'}")
        results["可用"].append("shell")
    else:
        print(f"[FAIL] shell: {error}")
        results["不可用"].append("shell")
    
    # superShell (JSON-RPC)
    try:
        result = d.jsonrpc.superShell("echo test")
        if result:
            print(f"[OK] jsonrpc.superShell: OK")
            results["可用"].append("jsonrpc.superShell")
        else:
            print(f"[WARN] jsonrpc.superShell: 返回空")
            results["部分可用"].append("jsonrpc.superShell")
    except Exception as e:
        print(f"[FAIL] jsonrpc.superShell: {e}")
        results["不可用"].append("jsonrpc.superShell")
    
    # ========== UI 选择器接口 ==========
    print("\n【UI 选择器接口】")
    print("-" * 60)
    
    # d(text=...)
    try:
        selector = d(text="test")
        # UiObject 总是会被创建，即使元素不存在，所以检查它是否有必要的方法
        if hasattr(selector, 'exists') and hasattr(selector, 'click'):
            print("[OK] d(text=...): 接口存在")
            results["可用"].append("selector")
        else:
            print("[FAIL] d(text=...): 接口不完整")
            results["不可用"].append("selector")
    except Exception as e:
        print(f"[FAIL] d(text=...): {e}")
        results["不可用"].append("selector")
    
    # ========== 应用管理接口 ==========
    print("\n【应用管理接口】")
    print("-" * 60)
    
    # app_current
    try:
        result = d.app_current()
        if result:
            print(f"[OK] app_current: {result.get('package', 'N/A')}")
            results["可用"].append("app_current")
        else:
            print("[WARN] app_current: 返回 None")
            results["部分可用"].append("app_current")
    except Exception as e:
        print(f"[FAIL] app_current: {e}")
        results["不可用"].append("app_current")
    
    # app_list_running
    try:
        result = d.app_list_running()
        if result:
            print(f"[OK] app_list_running: {len(result)} 个应用")
            results["可用"].append("app_list_running")
        else:
            print("[WARN] app_list_running: 返回空")
            results["部分可用"].append("app_list_running")
    except Exception as e:
        print(f"[FAIL] app_list_running: {e}")
        results["不可用"].append("app_list_running")
    
    # ========== 屏幕操作接口 ==========
    print("\n【屏幕操作接口】")
    print("-" * 60)
    
    # screen_on
    try:
        if hasattr(d, 'screen_on'):
            print("[OK] screen_on: 接口存在")
            results["可用"].append("screen_on")
        else:
            print("[FAIL] screen_on: 接口不存在")
            results["不可用"].append("screen_on")
    except Exception as e:
        print(f"[FAIL] screen_on: {e}")
        results["不可用"].append("screen_on")
    
    # screen_off
    try:
        if hasattr(d, 'screen_off'):
            print("[OK] screen_off: 接口存在")
            results["可用"].append("screen_off")
        else:
            print("[FAIL] screen_off: 接口不存在")
            results["不可用"].append("screen_off")
    except Exception as e:
        print(f"[FAIL] screen_off: {e}")
        results["不可用"].append("screen_off")
    
    # orientation
    try:
        result = d.orientation
        print(f"[OK] orientation: {result}")
        results["可用"].append("orientation")
    except Exception as e:
        print(f"[FAIL] orientation: {e}")
        results["不可用"].append("orientation")
    
    # dump_hierarchy
    success, result, error = test_interface("dump_hierarchy", lambda: d.dump_hierarchy(compressed=True))
    if success and result:
        print(f"[OK] dump_hierarchy: OK (长度: {len(result)} 字符)")
        results["可用"].append("dump_hierarchy")
    else:
        print(f"[FAIL] dump_hierarchy: {error}")
        results["不可用"].append("dump_hierarchy")
    
    # open_notification
    try:
        if hasattr(d, 'open_notification'):
            print("[OK] open_notification: 接口存在")
            results["可用"].append("open_notification")
        else:
            print("[FAIL] open_notification: 接口不存在")
            results["不可用"].append("open_notification")
    except Exception as e:
        print(f"[FAIL] open_notification: {e}")
        results["不可用"].append("open_notification")
    
    # open_quick_settings
    try:
        if hasattr(d, 'open_quick_settings'):
            print("[OK] open_quick_settings: 接口存在")
            results["可用"].append("open_quick_settings")
        else:
            print("[FAIL] open_quick_settings: 接口不存在")
            results["不可用"].append("open_quick_settings")
    except Exception as e:
        print(f"[FAIL] open_quick_settings: {e}")
        results["不可用"].append("open_quick_settings")
    
    # ========== JSON-RPC 接口测试 ==========
    print("\n【JSON-RPC 接口测试】")
    print("-" * 60)
    
    jsonrpc_methods = [
        "deviceInfo",
        "click",
        "swipe",
        "press",
        "dumpWindowHierarchy",
        "objInfo",
    ]
    
    for method in jsonrpc_methods:
        try:
            if method == "deviceInfo":
                result = d.jsonrpc.deviceInfo()
                print(f"[OK] jsonrpc.{method}: OK")
                results["可用"].append(f"jsonrpc.{method}")
            elif method == "click":
                # 只测试接口，不实际点击
                if hasattr(d.jsonrpc, method):
                    print(f"[OK] jsonrpc.{method}: 接口存在")
                    results["可用"].append(f"jsonrpc.{method}")
            elif method == "swipe":
                if hasattr(d.jsonrpc, method):
                    print(f"[OK] jsonrpc.{method}: 接口存在")
                    results["可用"].append(f"jsonrpc.{method}")
            elif method == "press":
                if hasattr(d.jsonrpc, method):
                    print(f"[OK] jsonrpc.{method}: 接口存在")
                    results["可用"].append(f"jsonrpc.{method}")
            elif method == "dumpWindowHierarchy":
                try:
                    result = d.jsonrpc.dumpWindowHierarchy(False, 50)
                    if result:
                        print(f"[OK] jsonrpc.{method}: OK")
                        results["可用"].append(f"jsonrpc.{method}")
                    else:
                        print(f"[WARN] jsonrpc.{method}: 返回空")
                        results["部分可用"].append(f"jsonrpc.{method}")
                except Exception as e:
                    print(f"[FAIL] jsonrpc.{method}: {e}")
                    results["不可用"].append(f"jsonrpc.{method}")
            else:
                if hasattr(d.jsonrpc, method):
                    print(f"[OK] jsonrpc.{method}: 接口存在")
                    results["可用"].append(f"jsonrpc.{method}")
        except Exception as e:
            print(f"[FAIL] jsonrpc.{method}: {e}")
            results["不可用"].append(f"jsonrpc.{method}")
    
    # ========== 插件接口 ==========
    print("\n【插件接口】")
    print("-" * 60)
    
    # xpath
    try:
        if hasattr(d, 'xpath'):
            print("[OK] xpath: 接口存在")
            results["可用"].append("xpath")
        else:
            print("[FAIL] xpath: 接口不存在")
            results["不可用"].append("xpath")
    except Exception as e:
        print(f"[FAIL] xpath: {e}")
        results["不可用"].append("xpath")
    
    # watcher
    try:
        if hasattr(d, 'watcher'):
            print("[OK] watcher: 接口存在")
            results["可用"].append("watcher")
        else:
            print("[FAIL] watcher: 接口不存在")
            results["不可用"].append("watcher")
    except Exception as e:
        print(f"[FAIL] watcher: {e}")
        results["不可用"].append("watcher")
    
    # screenrecord
    try:
        if hasattr(d, 'screenrecord'):
            print("[OK] screenrecord: 接口存在")
            results["可用"].append("screenrecord")
        else:
            print("[FAIL] screenrecord: 接口不存在")
            results["不可用"].append("screenrecord")
    except Exception as e:
        print(f"[FAIL] screenrecord: {e}")
        results["不可用"].append("screenrecord")
    
    # swipe_ext
    try:
        if hasattr(d, 'swipe_ext'):
            print("[OK] swipe_ext: 接口存在")
            results["可用"].append("swipe_ext")
        else:
            print("[FAIL] swipe_ext: 接口不存在")
            results["不可用"].append("swipe_ext")
    except Exception as e:
        print(f"[FAIL] swipe_ext: {e}")
        results["不可用"].append("swipe_ext")
    
    # ========== 其他接口测试 ==========
    print("\n【其他接口测试】")
    print("-" * 60)
    
    # drag
    try:
        if hasattr(d, 'drag'):
            print("[OK] drag: 接口存在")
            results["可用"].append("drag")
        else:
            print("[FAIL] drag: 接口不存在")
            results["不可用"].append("drag")
    except Exception as e:
        print(f"[FAIL] drag: {e}")
        results["不可用"].append("drag")
    
    # unlock
    try:
        if hasattr(d, 'unlock'):
            print("[OK] unlock: 接口存在")
            results["可用"].append("unlock")
        else:
            print("[FAIL] unlock: 接口不存在")
            results["不可用"].append("unlock")
    except Exception as e:
        print(f"[FAIL] unlock: {e}")
        results["不可用"].append("unlock")
    
    # clipboard
    try:
        clipboard_value = d.clipboard
        print(f"[OK] clipboard: {clipboard_value[:50] if clipboard_value else 'None'}")
        results["可用"].append("clipboard")
    except Exception as e:
        print(f"[FAIL] clipboard: {e}")
        results["不可用"].append("clipboard")
    
    # last_toast
    try:
        toast = d.last_toast
        print(f"[OK] last_toast: {toast[:50] if toast else 'None'}")
        results["可用"].append("last_toast")
    except Exception as e:
        print(f"[FAIL] last_toast: {e}")
        results["不可用"].append("last_toast")
    
    # ========== 总结 ==========
    print("\n" + "=" * 60)
    print("【测试总结】")
    print("=" * 60)
    
    total = len(results['可用']) + len(results['部分可用']) + len(results['不可用'])
    
    print(f"\n[OK] 可用接口 ({len(results['可用'])}/{total}):")
    for item in sorted(results["可用"]):
        print(f"  - {item}")
    
    if results["部分可用"]:
        print(f"\n[WARN] 部分可用接口 ({len(results['部分可用'])}/{total}):")
        for item in sorted(results["部分可用"]):
            print(f"  - {item}")
    
    if results["不可用"]:
        print(f"\n[FAIL] 不可用接口 ({len(results['不可用'])}/{total}):")
        for item in sorted(results["不可用"]):
            print(f"  - {item}")
    
    if total > 0:
        available_rate = len(results['可用']) / total * 100
        print(f"\n可用率: {available_rate:.1f}% ({len(results['可用'])}/{total})")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()


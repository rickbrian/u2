#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
纯协议投屏程序 - 使用 JSON-RPC 协议直接与设备通信
不依赖 uiautomator2 源码，仅使用标准库和第三方库
"""

import json
import time
import cv2
import threading
import base64
import numpy as np
from queue import Queue
import requests
from typing import Optional, Tuple, Any



class U2RPCClient:
    """uiautomator2 JSON-RPC 客户端（纯协议实现）"""
    
    def __init__(self, host: str, port: int = 9008, timeout: float = 10.0):
        """
        Args:
            host: 设备 IP 地址
            port: 设备端口（默认 9008）
            timeout: 请求超时时间（秒）
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self._rpc_id = 1
        
        # 检查服务器是否可用
        self._check_alive()
    
    def _check_alive(self):
        """检查服务器是否可用"""
        try:
            response = requests.get(
                f"{self.base_url}/ping",
                timeout=2.0,
                headers={'User-Agent': 'uiautomator2', 'Accept-Encoding': ''}
            )
            if response.content != b"pong":
                raise ConnectionError(f"Server ping failed: {response.content}")
        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to uiautomator2 server at {self.host}:{self.port}. "
                f"Make sure u2.jar is running on the device. Error: {e}"
            )
    
    def _jsonrpc_call(self, method: str, params: Any = None) -> Any:
        """
        调用 JSON-RPC 方法
        
        Args:
            method: JSON-RPC 方法名
            params: 方法参数（可以是列表、字典或 None）
            
        Returns:
            JSON-RPC 响应的 result 字段
        """
        # 构建 JSON-RPC 2.0 请求
        payload = {
            "jsonrpc": "2.0",
            "id": self._rpc_id,
            "method": method,
            "params": params if params is not None else []
        }
        self._rpc_id += 1
        
        # 发送 HTTP POST 请求
        headers = {
            'User-Agent': 'uiautomator2',
            'Accept-Encoding': '',  # 避免 gzip 压缩（nanohttpd 有资源泄漏问题）
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/jsonrpc/0",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 解析 JSON 响应
            data = response.json()
            
            # 检查错误
            if "error" in data:
                error = data["error"]
                code = error.get('code', -1)
                message = error.get('message', 'Unknown error')
                raise RuntimeError(f"JSON-RPC error [{code}]: {message}")
            
            # 返回结果
            if "result" not in data:
                raise RuntimeError("JSON-RPC response missing 'result' field")
            
            return data["result"]
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"HTTP request failed: {e}")
    
    def take_screenshot(self, scale: float = 1.0, quality: int = 80) -> Optional[str]:
        """
        截取屏幕截图
        
        Args:
            scale: 缩放比例（1.0 = 100%, 0.5 = 50%, 2.0 = 200%）
            quality: JPEG 压缩质量（0-100，80 表示 80% 质量）
            
        Returns:
            Base64 编码的 JPEG 图片数据，失败返回 None
        """
        try:
            result = self._jsonrpc_call("takeScreenshot", [scale, quality])
            return result
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return None
    
    def device_info(self) -> dict:
        """
        获取设备信息
        
        Returns:
            设备信息字典
        """
        return self._jsonrpc_call("deviceInfo")
    
    def click(self, x: int, y: int) -> bool:
        """
        点击设备屏幕指定位置
        
        Args:
            x: X 坐标（设备绝对坐标）
            y: Y 坐标（设备绝对坐标）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            self._jsonrpc_call("click", [x, y])
            return True
        except Exception as e:
            print(f"Click failed: {e}")
            return False
    
    def swipe(self, fx: int, fy: int, tx: int, ty: int, steps: int = 10) -> bool:
        """
        滑动操作
        
        Args:
            fx: 起始 X 坐标（设备绝对坐标）
            fy: 起始 Y 坐标（设备绝对坐标）
            tx: 结束 X 坐标（设备绝对坐标）
            ty: 结束 Y 坐标（设备绝对坐标）
            steps: 滑动步数（默认 10，每步约 5ms）
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            self._jsonrpc_call("swipe", [fx, fy, tx, ty, steps])
            return True
        except Exception as e:
            print(f"Swipe failed: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """
        按下按键
        
        Args:
            key: 按键名称，如 "back", "home", "menu" 等
            
        Returns:
            成功返回 True，失败返回 False
        """
        try:
            self._jsonrpc_call("pressKey", [key])
            return True
        except Exception as e:
            print(f"Press key failed: {e}")
            return False
    
    def swipe_ext(self, direction: str, scale: float = 0.9, box: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        扩展滑动操作（类似 uiautomator2 的 swipe_ext）
        
        Args:
            direction: 滑动方向，"up", "down", "left", "right"
            scale: 滑动距离比例（0-1），0.9 表示滑动距离为屏幕尺寸的 90%
            box: 滑动区域 [lx, ly, rx, ry]，None 表示全屏
            
        Returns:
            成功返回 True，失败返回 False
        """
        # 获取设备尺寸
        info = self.device_info()
        device_w = info.get('displayWidth', 1080)
        device_h = info.get('displayHeight', 2240)
        
        # 确定滑动区域
        if box:
            lx, ly, rx, ry = box
        else:
            lx, ly = 0, 0
            rx, ry = device_w, device_h
        
        width = rx - lx
        height = ry - ly
        
        # 计算偏移量
        h_offset = int(width * (1 - scale) // 2)
        v_offset = int(height * (1 - scale) // 2)
        
        # 计算滑动起点和终点
        center_x = lx + width // 2
        center_y = ly + height // 2
        
        if direction == "up":
            # 向上滑动：从中心滑动到顶部（屏幕内容向上移动）
            fx, fy = center_x, center_y
            tx, ty = center_x, ly + v_offset
        elif direction == "down":
            # 向下滑动：从中心滑动到底部（屏幕内容向下移动）
            fx, fy = center_x, center_y
            tx, ty = center_x, ry - v_offset
        elif direction == "left":
            # 向左滑动：从右侧滑动到左侧
            fx, fy = rx - h_offset, center_y
            tx, ty = lx + h_offset, center_y
        elif direction == "right":
            # 向右滑动：从左侧滑动到右侧
            fx, fy = lx + h_offset, center_y
            tx, ty = rx - h_offset, center_y
        else:
            raise ValueError(f"Unknown direction: {direction}")
        
        return self.swipe(fx, fy, tx, ty, steps=10)


def main():
    # 设备地址（WiFi 模式）
    # device_host = "10.196.144.39"
    device_host = "192.168.25.22"
    device_port = 9008
    
    print(f"正在连接设备: {device_host}:{device_port}")
    try:
        client = U2RPCClient(device_host, device_port)
        print("连接成功！")
    except Exception as e:
        print(f"连接失败: {e}")
        return
    
    # 获取设备屏幕尺寸
    try:
        info = client.device_info()
        screen_width = info.get('displayWidth', 0)
        screen_height = info.get('displayHeight', 0)
        print(f"设备信息: {screen_width}x{screen_height}")
    except Exception as e:
        print(f"获取设备信息失败: {e}")
        # 尝试从截图获取尺寸
        try:
            base64_data = client.take_screenshot(1.0, 80)
            if base64_data:
                jpg_raw = base64.b64decode(base64_data)
                nparr = np.frombuffer(jpg_raw, np.uint8)
                test_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if test_img is not None:
                    screen_height, screen_width = test_img.shape[:2]
                    print(f"从截图获取设备尺寸: {screen_width}x{screen_height}")
                else:
                    screen_width, screen_height = 1080, 1920
            else:
                screen_width, screen_height = 1080, 1920
        except:
            screen_width, screen_height = 1080, 1920
    
    print("开始投屏...")
    print("操作说明：")
    print("  - 左键点击：点击投屏对应位置")
    print("  - 右键点击：返回键（back）")
    print("  - 鼠标滚轮：向上/向下滚动屏幕")
    print("  - 按 'q' 键：退出程序")
    print("  - 点击窗口 X：关闭程序")
    
    window_name = "UIAutomator2 desk"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # 设置窗口初始大小，保持设备屏幕比例
    max_display_width = 1680
    max_display_height = 810
    
    if screen_width > 0 and screen_height > 0:
        aspect_ratio = screen_width / screen_height
        
        if screen_width > max_display_width:
            display_width = max_display_width
            display_height = int(max_display_width / aspect_ratio)
        elif screen_height > max_display_height:
            display_height = max_display_height
            display_width = int(max_display_height * aspect_ratio)
        else:
            display_width = screen_width
            display_height = screen_height
        
        cv2.resizeWindow(window_name, display_width, display_height)
        print(f"窗口尺寸: {display_width}x{display_height}")
    
    # 性能优化参数
    SCREENSHOT_QUALITY = 50  # 降低质量到50，减少传输数据量
    SCREENSHOT_SCALE = 0.8   # 使用0.8倍缩放，进一步减少数据量
    QUEUE_SIZE = 1           # 队列大小设为1，只保留最新帧，减少内存占用
    
    # 使用队列进行多线程处理
    screenshot_queue = Queue(maxsize=QUEUE_SIZE)
    running = threading.Event()
    running.set()
    
    frame_count = 0
    start_time = time.time()
    last_fps_update = time.time()
    current_fps = 0.0
    
    # 坐标转换相关变量（需要在回调中使用）
    current_screenshot = None  # 当前显示的截图
    screenshot_lock = threading.Lock()  # 保护共享变量的锁
    
    def mouse_callback(event, x, y, flags, param):
        """鼠标事件回调函数"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # 左键点击
            # OpenCV 的鼠标回调函数返回的坐标是屏幕坐标，直接使用作为设备坐标
            client.click(x, y)
        
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 右键点击 -> 返回键
            client.press_key("back")
        
        elif event == cv2.EVENT_MOUSEWHEEL:
            # 鼠标滚轮事件（Windows）
            # flags 的高 16 位包含滚轮增量
            # delta > 0: 向上滚动（滚轮向上）
            # delta < 0: 向下滚动（滚轮向下）
            delta = flags >> 16
            
            if delta > 0:
                # 向上滚动滚轮 -> 屏幕内容向上移动（向下滑动）
                client.swipe_ext("down", scale=0.5)
            elif delta < 0:
                # 向下滚动滚轮 -> 屏幕内容向下移动（向上滑动）
                client.swipe_ext("up", scale=0.4)
    
    # 设置鼠标回调
    cv2.setMouseCallback(window_name, mouse_callback)
    
    def screenshot_thread():
        """截图线程，持续获取截图"""
        while running.is_set():
            try:
                # 截屏（优化：降低质量和尺寸）
                base64_data = client.take_screenshot(SCREENSHOT_SCALE, SCREENSHOT_QUALITY)
                if base64_data:
                    # 直接使用 cv2.imdecode，比 PIL + image_convert 更快
                    jpg_raw = base64.b64decode(base64_data)
                    # 使用 cv2.imdecode 直接解码为 numpy 数组
                    nparr = np.frombuffer(jpg_raw, np.uint8)
                    screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if screenshot is not None:
                        # 如果队列满了，丢弃最旧的帧（保持最新）
                        if screenshot_queue.full():
                            try:
                                screenshot_queue.get_nowait()
                            except:
                                pass
                        screenshot_queue.put(screenshot, timeout=0.05)
                else:
                    time.sleep(0.005)  # 减少等待时间
            except Exception:
                time.sleep(0.005)
    
    # 启动截图线程
    screenshot_thread_obj = threading.Thread(target=screenshot_thread, daemon=True)
    screenshot_thread_obj.start()
    
    try:
        window_initialized = False  # 标记窗口是否已经显示过内容
        while True:
            try:
                # 从队列获取最新截图（非阻塞）
                screenshot = None
                try:
                    screenshot = screenshot_queue.get_nowait()
                except:
                    pass
                
                if screenshot is not None:
                    frame_count += 1
                    window_initialized = True  # 窗口已经显示过内容
                    
                    # 更新当前截图（用于坐标转换）
                    with screenshot_lock:
                        current_screenshot = screenshot.copy()
                    
                    # 每0.5秒更新一次FPS显示
                    now = time.time()
                    if now - last_fps_update >= 0.5:
                        elapsed = now - start_time
                        if elapsed > 0:
                            current_fps = frame_count / elapsed
                        last_fps_update = now
                    
                    # 显示FPS和提示信息（直接在原图上绘制）
                    display_img = screenshot.copy()
                    if current_fps > 0:
                        cv2.putText(display_img, f"FPS: {current_fps:.1f}", (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(display_img, "左键点击 | 右键返回 | 滚轮滚动 | 按'q'退出", (10, display_img.shape[0] - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # 显示图片
                    cv2.imshow(window_name, display_img)
                
                # 检查按键和窗口状态
                # 注意：cv2.waitKey() 在窗口刚创建时也会返回 -1，所以需要先显示内容后再检查
                key = cv2.waitKey(1)
                if window_initialized:
                    # 只有在窗口已经显示过内容后，才检查窗口是否关闭
                    # 使用 getWindowProperty 更可靠地检测窗口关闭
                    try:
                        window_prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                        if window_prop is None or (isinstance(window_prop, (int, float)) and window_prop <= 0):
                            print("检测到窗口已关闭")
                            break
                    except Exception:
                        # 窗口不存在时也会抛出异常
                        print("窗口不存在")
                        break
                
                # 检查按键
                if key != -1 and key & 0xFF == ord('q'):
                    print("退出投屏")
                    break
                
            except KeyboardInterrupt:
                break
            except Exception:
                pass  # 静默处理异常，不输出
                
    finally:
        # 停止截图线程
        running.clear()
        screenshot_thread_obj.join(timeout=1.0)
        # 关闭窗口
        try:
            cv2.destroyWindow(window_name)
        except:
            pass
        try:
            cv2.destroyAllWindows()
        except:
            pass
        print("投屏结束")


if __name__ == "__main__":
    main()


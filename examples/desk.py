#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简易投屏程序 - 循环截屏并实时显示（极致性能优化版）
"""

import sys
import os
import time
import cv2
import threading
import base64
import numpy as np
from queue import Queue

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uiautomator2 as u2


def main():
    # 设备地址（WiFi 模式）
    device_address = "10.196.144.39:9008"
    
    print(f"正在连接设备: {device_address}")
    try:
        d = u2.connect_wifi(device_address)
        print("连接成功！")
    except Exception as e:
        print(f"连接失败: {e}")
        return
    
    # 获取设备屏幕尺寸
    try:
        info = d.info
        screen_width = info.get('displayWidth', 0)
        screen_height = info.get('displayHeight', 0)
        print(f"设备信息: {screen_width}x{screen_height}")
    except Exception as e:
        print(f"获取设备信息失败: {e}")
        try:
            test_img = d.screenshot(format='opencv')
            if test_img is not None:
                screen_height, screen_width = test_img.shape[:2]
                print(f"从截图获取设备尺寸: {screen_width}x{screen_height}")
            else:
                screen_width, screen_height = 1080, 1920
        except:
            screen_width, screen_height = 1080, 1920
    
    print("开始投屏... (按 'q' 键退出或点击窗口 X 关闭)")
    
    window_name = "UIAutomator2 投屏"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # 设置窗口初始大小，保持设备屏幕比例
    max_display_width = 1200
    max_display_height = 800
    
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
    SCREENSHOT_SCALE = 0.8   # 使用0.8倍缩放，进一步减少数据量（可选）
    QUEUE_SIZE = 1           # 队列大小设为1，只保留最新帧，减少内存占用
    
    # 使用队列进行多线程处理
    screenshot_queue = Queue(maxsize=QUEUE_SIZE)
    running = threading.Event()
    running.set()
    
    frame_count = 0
    start_time = time.time()
    last_fps_update = time.time()
    current_fps = 0.0
    
    def screenshot_thread():
        """截图线程，持续获取截图"""
        check_counter = 0
        while running.is_set():
            try:
                # 降低窗口检查频率（每10次检查一次）
                check_counter += 1
                if check_counter >= 10:
                    try:
                        window_prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                        if window_prop is None or (isinstance(window_prop, (int, float)) and window_prop <= 0):
                            break
                    except Exception:
                        break
                    check_counter = 0
                
                # 截屏（优化：降低质量和尺寸）
                try:
                    # 使用较低的质量和缩放比例
                    base64_data = d.jsonrpc.takeScreenshot(SCREENSHOT_SCALE, SCREENSHOT_QUALITY)
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
                    
            except Exception:
                time.sleep(0.005)
    
    # 启动截图线程
    screenshot_thread_obj = threading.Thread(target=screenshot_thread, daemon=True)
    screenshot_thread_obj.start()
    
    try:
        while True:
            try:
                # 每次循环都检查窗口状态（确保及时响应窗口关闭）
                try:
                    window_prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                    if window_prop is None or (isinstance(window_prop, (int, float)) and window_prop <= 0):
                        print("检测到窗口已关闭")
                        break
                except Exception:
                    # 窗口不存在时也会抛出异常
                    print("窗口不存在")
                    break
                
                # 从队列获取最新截图（非阻塞）
                screenshot = None
                try:
                    screenshot = screenshot_queue.get_nowait()
                except:
                    pass
                
                if screenshot is not None:
                    frame_count += 1
                    
                    # 每0.5秒更新一次FPS显示
                    now = time.time()
                    if now - last_fps_update >= 0.5:
                        elapsed = now - start_time
                        if elapsed > 0:
                            current_fps = frame_count / elapsed
                        last_fps_update = now
                    
                    # 显示FPS（直接在原图上绘制，因为这是显示用的）
                    if current_fps > 0:
                        cv2.putText(screenshot, f"FPS: {current_fps:.1f}", (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # 显示图片
                    cv2.imshow(window_name, screenshot)
                
                # 检查按键（使用非阻塞模式）
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("退出投屏")
                    break
                
                # 在 waitKey 之后再次检查窗口状态（窗口可能在显示过程中被关闭）
                try:
                    window_prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                    if window_prop is None or (isinstance(window_prop, (int, float)) and window_prop <= 0):
                        break
                except Exception:
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

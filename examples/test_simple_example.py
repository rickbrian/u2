# coding: utf-8
#
import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uiautomator2 as u2


def test_simple():
    d = u2.connect_wifi("192.168.25.22:9008")

    d.press("back")
    d(text="OK").exists
    # t =d(text="取消").sibling(className="android.widget.Button").info
    # print(t)

    # d(text="Enter PIN").wait(timeout=5)


if __name__ == "__main__":
    test_simple()


"""
-*- coding: utf-8 -*-

@File: active.py
@author: 我的小熊掉了
@time: 2025/1/14 14:58
"""
import time
from typing import List, Optional, Tuple
from connect import execute_cmd, connect_mumu_emulator, end_connect, screen_shot, adb
from targetMatch import img_Match
import cv2


def click(x, y):
    """

    :param x: 点击的x坐标
    :param y: 点击的y坐标
    :return: 执行为真
    """
    result = execute_cmd([adb, 'shell', 'input', 'tap', f'{x}', f'{y}'], 'click')
    if result.returncode == 0:
        return True
    else:
        return False


def slide(x1, y1, x2, y2):
    """
    从(x1,y1)滑动到(x2,y2)
    :param x1: 移动的x1坐标
    :param y1: 移动的y1坐标
    :param x2: 移动的x2坐标
    :param y2: 移动的y2坐标
    :return: 执行为真
    """
    result = execute_cmd([adb, 'shell', 'input', 'swipe', f'{x1}', f'{y1}', f'{x2}', f'{y2}'], 'slide')
    if result.returncode == 0:
        return True
    else:
        return False


def back_press():  # 模拟按下Android设备的返回键
    """
    :return:执行为真
    """
    result = execute_cmd([adb, 'shell', 'input', 'keyevent', 'KEYCODE_BACK'], 'lift')
    if result.returncode == 0:
        return True
    else:
        return False


def DPAD_CENTER_press(): # 模拟按下Android设备的导航键 确定键
    """
    :return: 执行为真
    """
    result = execute_cmd([adb, 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 'press')
    if result.returncode == 0:
        return True
    else:
        return False


def active_data(matchData: str):
    """

    :param matchData: 对比图片路径
    :return:执行为真
    """
    screenShot = screen_shot()  # 捕获屏幕截图
    a = cv2.imread(matchData, 0)  # 读取需要对比的图片
    matchBool, co = img_Match(a, screenShot)  # 从屏幕上寻找需要操作的坐标co[0],co[1]
    if matchBool:
        click(co[0], co[1])
        return True
    else:
        print('没有找到对比图片')
        return False


if __name__ == '__main__':
    connect_mumu_emulator(16384)
    end_connect()

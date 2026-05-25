"""
-*- coding: utf-8 -*-

@File: package.py
@author: 我的小熊掉了
@time: 2025/1/14 10:18
"""
import re
import time
import active
import connect
from connect import adb
import targetMatch
import subprocess
import cv2
from paddleocr import PaddleOCR


arknights_offical = 'com.hypergryph.arknights'
arknights_offical_activity = 'com.u8.sdk.U8UnityContext'  # 打开应用，使用get_current_focus_window获取返回值得到activity
arknights_bilibili = 'com.hypergryph.arknights.bilibili'
arknights_bilibili_activity = 'com.u8.sdk.U8UnityContext'


def get_current_focus_window():
    """
    获取当前焦点窗口的应用信息

    参数:
        device_address: 设备地址 (如: "127.0.0.1:7555" 对于 MuMu 模拟器)

    返回:
        包含包名和活动名的字典，或 None 如果未找到
    """
    try:
        # 构造基础命令
        base_cmd = [adb]

        # 完整命令
        cmd = base_cmd + ['shell', 'dumpsys', 'window']

        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )

        # 检查命令是否执行成功
        if result.returncode != 0:
            print(f"命令执行失败，错误码: {result.returncode}")
            print(f"错误输出: {result.stderr}")
            return None

        # 在输出中查找 mCurrentFocus 行
        for line in result.stdout.splitlines():
            if 'mCurrentFocus' in line:
                # 使用正则表达式提取包名和活动名
                match = re.search(r'([a-zA-Z0-9._]+)/([a-zA-Z0-9._]+)', line)
                if match:
                    return {
                        'package': match.group(1),
                        'activity': match.group(2)
                    }
                else:
                    # 尝试其他格式的匹配
                    match = re.search(r'([a-zA-Z0-9._]+)\.[a-zA-Z0-9_]+', line)
                    if match:
                        return {
                            'package': match.group(1),
                            'activity': 'Unknown'
                        }

        print("未找到 mCurrentFocus 信息")
        return None

    except subprocess.TimeoutExpired:
        print("命令执行超时")
        return None
    except FileNotFoundError:
        print("错误: adb命令未找到，请确保已安装Android SDK并配置环境变量")
        return None
    except Exception as e:
        print(f"未知错误: {str(e)}")
        return None


def close_arknights():
    """
    强制关闭明日方舟应用

    参数:
        device_serial: 设备序列号(可选，用于多设备情况)

    返回:
        tuple: (是否成功, 消息)
    """
    package_name = 'com.hypergryph.arknights.bilibili'

    try:
        # 构造基础命令
        base_cmd = [adb]
        # 强制停止应用
        cmd = base_cmd + ['shell', 'am', 'force-stop', package_name]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return True, f"成功关闭应用: {package_name}"
        return False, f"关闭失败: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "命令执行超时"
    except Exception as e:
        return False, f"关闭异常: {str(e)}"


def gracefully_close_arknights(max_attempts=5):
    """
    优雅关闭应用(模拟返回键)

    参数:
        device_serial: 设备序列号
        max_attempts: 最大尝试次数

    返回:
        tuple: (是否成功, 消息)
    """
    package_name = 'com.hypergryph.arknights.bilibili'
    activity_name = 'com.u8.sdk.U8UnityContext'

    try:
        base_cmd = [adb]

        # 尝试优雅退出
        for i in range(max_attempts):
            print(f'尝试第{i}次')
            if not is_application_operation():
                return True
            # 发送返回键
            subprocess.run(
                base_cmd + ['shell', 'input', 'keyevent', 'KEYCODE_BACK'],
                timeout=5
            )
            time.sleep(1)  # 等待响应

        # 如果优雅退出失败，强制停止
        return close_arknights()

    except Exception as e:
        return False, f"关闭异常: {str(e)}"


def close_arknights_complete():
    """
    完整的关闭明日方舟流程

    参数:
        mumu_index: 模拟器索引(0表示第一个)

    返回:
        tuple: (是否成功, 消息)
    """

    # 先尝试优雅关闭
    success, msg = gracefully_close_arknights()
    if success:
        return True, msg

    # 优雅关闭失败则强制停止
    return close_arknights()


def is_application_operation(package_name=arknights_bilibili):
    print('检测明日方舟是否运行')
    try:
        cmd = [adb] + ['shell', 'am', 'stack', 'list', '|', 'grep', package_name]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=10
        )

        if package_name in result.stdout:
            print('明日方舟正在运行')
            return True
        print('明日方舟没有运行，准备启动')
        return False

    except subprocess.TimeoutExpired:
        return False, "命令执行超时"

    except Exception as e:
        return False, f"错误: {str(e)}"


if __name__ == '__main__':
    level_name = 'BI - 6'

    connect.connect_mumu_emulator(16384)  # 连接到模拟器

    a = get_current_focus_window()
    print(a)
    connect.end_connect()  # 结束连接




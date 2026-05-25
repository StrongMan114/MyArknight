"""
-*- coding: utf-8 -*-

@File: targetMatch.py
@author: 我的小熊掉了
@time: 2024/10/29 10:24
"""

import subprocess
import os
import time
import cv2

portList = [16384, 16416, 16448, 16480, 16512, 16544, 16576]
adb = r'D:\MuMuPlayer-12.0\nx_device\12.0\shell\adb.exe'

# mumuPath = r'D:\MuMuPlayer-12.0\shell\MuMuPlayer.exe'


def execute_cmd(argsList, record):
    """

    :param argsList: 命令列表
    :param record: 命令名称
    :return: 命令返回值
    """
    try:
        if type(argsList) is list:
            result = subprocess.run(argsList, capture_output=True)
        elif type(argsList) is str:
            argsList = argsList.split(' ')[1:]
            argsList = [adb] + argsList
            # 执行ADB命令并捕获输出
            result = subprocess.run(
                argsList,
                capture_output=True,
                shell=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                check=True
            )
        else:
            result = None

    except subprocess.CalledProcessError as e:
        print(f"命令执行失败,出现错误: {e.stderr}")
        return []
    except FileNotFoundError:
        print("错误: adb命令未找到，请确保已安装Android SDK并配置环境变量")
        return []
    except Exception as e:
        print(f"未知错误: {str(e)}")
        return []

    if result.returncode == 0:
        # print(f"命令执行成功{record}")
        pass
    else:
        print(f"命令执行失败{record}，错误码{result.returncode}")

    return result


def start_mumu_emulator(workPath=r'D:\MuMuPlayer - 12.0\shell\MuMuPlayer.exe'):
    """

    :param workPath: 模拟器exe路径
    :return: None
    """
    os.system(workPath)
    return None


def connect_mumu_emulator(port):
    """
    连接到模拟器
    :param port: 端口号
    :return: Bool
    """
    # execute_cmd([adb, 'kill-server'], 'kill')
    # execute_cmd([adb, 'start-server'], 'start')
    execute_cmd([adb, 'devices'], 'device')
    result = execute_cmd([adb, 'connect', f'127.0.0.1:{port}'], 'connect')
    if result.returncode == 0:
        return True
    else:
        return False


def start_arknights_bilibili():
    arknights_bilibili = 'com.hypergryph.arknights.bilibili'
    arknights_bilibili_activity = 'com.u8.sdk.U8UnityContext'
    result = execute_cmd(f'adb shell am start -n {arknights_bilibili}/{arknights_bilibili_activity} -W',
                         'start_arknights_offical')
    if result.returncode == 0:
        print('启动成功')
        return True
    else:
        print('启动失败')
        return False


def end_connect():
    """ 关闭adb连接 """
    execute_cmd([adb, 'kill-server'], 'kill')


# def screen_shot(path: str = 'image/screen.png', read=0):
#     """截图，返回截取的图片"""
#     execute_cmd([adb, 'shell', 'screencap', '/sdcard/screen.png'], 'screenPNG')
#     execute_cmd([adb, 'pull', '/sdcard/screen.png', path], 'pullPNG')
#
#     screen_picture = cv2.imread(path, read)
#     return screen_picture


# 直接截屏到本地
def screen_shot_local(path: str = r'E:\bishe\learn\MyArknights\opencv\image\screen.png', read=0):
    """截图，返回截取的图片"""
    cmd = f'{adb} -s emulator-5554 exec-out screencap -p > "{path}"'
    execute_cmd(cmd, 'screenPNG')

    screen_picture = cv2.imread(path, read)
    return screen_picture


def screen_shot(local_path: str = 'image/screen.png', read=0):
    device_serial = 'emulator-5554'
    remote_path = '/sdcard/screen.png'
    # local_path = r'E:\bishe\learn\MyArknights\opencv\image\screen.png'

    try:
        # 1. 在设备上截图
        screenshot_result = subprocess.run(
            [adb, '-s', device_serial, 'shell', 'screencap', '-p', remote_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if screenshot_result.returncode != 0:
            print(f"截图失败: {screenshot_result.stderr}")
            return False

        # 等待文件写入完成
        time.sleep(0.5)

        # 2. 将截图拉取到本地
        pull_result = subprocess.run(
            [adb, '-s', device_serial, 'pull', remote_path, local_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if pull_result.returncode != 0:
            print(f"拉取失败: {pull_result.stderr}")
            return None

        screen_picture = cv2.imread(local_path, read)

        return screen_picture

    except subprocess.TimeoutExpired:
        print("命令执行超时")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None


if __name__ == '__main__':
    # 启动模拟器
    # mumuPath = r'D:\MuMuPlayer-12.0\shell\MuMuPlayer.exe'
    # execute_cmd([mumuPath], 'startMumu')

    a = connect_mumu_emulator(16384)
    print(a)
    png = screen_shot()

    cv2.imshow('pullPng', png)
    cv2.waitKey()

    time.sleep(2)
    end_connect()

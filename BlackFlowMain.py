"""
@File  ：BlackFlowMain.py
@Python：3.10
@Author：我的小熊掉了
@Date  ：2026/7/20 10:36

"""

import os
import subprocess
import shutil
import tempfile
import time
import logging

import psutil

logging.disable(logging.DEBUG)  # 关闭DEBUG日志的打印
logging.disable(logging.WARNING)  # 关闭WARNING日志的打印
os.environ['FLAGS_allocator_strategy'] = 'naive_best_fit'

import sys

sys.path.append('./my_utils')
import gc

from memory_profiler import profile
import cv2
import numpy as np
import paddle
from paddleocr import PaddleOCR
import difflib
from collections import deque

import main_start
from my_utils import targetMatch
from my_utils import active
from my_utils import connect
import jieGarden_active
import BlackFlowActive

script_temp = r'D:\My Games\arknights_script'
os.makedirs(script_temp, exist_ok=True)

# 覆盖系统临时目录
os.environ['TMP'] = script_temp
os.environ['TEMP'] = script_temp
os.environ['TMPDIR'] = script_temp
tempfile.tempdir = script_temp

# Paddle 缓存
os.environ['PADDLE_CACHE_DIR'] = os.path.join(script_temp, 'paddle_cache')
os.makedirs(os.environ['PADDLE_CACHE_DIR'], exist_ok=True)

# 禁用 Paddle 日志减少碎片
os.environ['GLOG_logtostderr'] = '0'
os.environ['GLOG_v'] = '0'

os.environ["FLAGS_allocator_strategy"] = "naive_best_fit"
os.environ["FLAGS_fraction_of_gpu_memory_to_use"] = "0.2"

EPOCH = 30  # 循环轮数


def load_all_templates():
    """统一加载模板图像，避免重复读取"""
    return {
        "team_enter": cv2.imread('rogue_blackflow/team_enter.png', 0),
        "team_quit": cv2.imread('rogue_blackflow/quit_enter.png', 0),
        "map_lower": cv2.imread('rogue_blackflow/litter.png', 0),
        "map_check": cv2.imread('rogue_blackflow/map_check.png', 0),
        "event_exit": cv2.imread('rogue_blackflow/event_quit.png', 0),
        "exit": cv2.imread('rogue_blackflow/exit.png', 0),
        "game_quit": cv2.imread('rogue_blackflow/quit_enter.png', 0),
        "epoch_end_enter": cv2.imread('rogue_blackflow/game_over.png', 0)
    }


class OCRManager:
    _instance = None
    _ocr = None
    _call_count = 0  # 调用计数器
    _RESET_THRESHOLD = 15  # 每15次调用强制重建

    def get_ocr(self):
        if self._ocr is None:
            print("初始化 PaddleOCR...")
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                enable_mkldnn=True,
                mkldnn_cache_capacity=10,
                lang='ch',
                show_log=False,  # 关闭内部日志，减少内存碎片
                use_gpu=False  # 如果不用GPU，强制CPU推理更稳定
            )
            self._call_count = 0
        return self._ocr

    def force_restart(self):
        """完全销毁 OCR 实例，释放所有内存"""
        if self._ocr is not None:
            # 1. 删除引用
            del self._ocr
            self._ocr = None

            # 2. 强制 Python 垃圾回收
            gc.collect()

            # 3. 清理 Paddle 底层缓存（关键）
            try:
                import paddle
                if paddle.device.is_compiled_with_cuda():
                    paddle.device.cuda.empty_cache()
                # 清理全局内存池
                paddle.framework._dygraph_tracer().clear_cache()

            except Exception as e:
                print(f"清理Paddle缓存异常: {e}")

            # 4. 等待内存回收
            time.sleep(2)

            # 5. 重新初始化
            self.get_ocr()
            print("OCR 已完全重启，内存已释放")


def clear_console_ansi():
    """使用 ANSI 转义清空控制台"""
    # \033[2J 清空屏幕
    # \033[H 将光标移到左上角
    print('\033[2J\033[H', end='')
    sys.stdout.flush()


def clear_temp():

    temp_dir=tempfile.gettempdir()

    for name in os.listdir(temp_dir):

        path=os.path.join(temp_dir,name)

        try:
            if os.path.isfile(path):
                os.remove(path)

            elif os.path.isdir(path):
                shutil.rmtree(path)

        except:
            pass


def main_loop(ocr, templates, height, width, max_rounds=100):
    """
    :param ocr: ocr模型
    :param templates: load_all_templates()加载的图片
    :param height: 模拟器分辨率 高
    :param width: 模拟器分辨率 宽
    :param max_rounds: 最大循环次数
    :return: None
    """

    time_start = time.time()
    ocr_manager.force_restart()
    ocr = ocr_manager.get_ocr()

    try:
        # 1. --- 进入本局 ---
        cor = BlackFlowActive.start(ocr, '开始探索', '堡垒战术分队')  # 开始探索
        jieGarden_active.select_team(templates["team_enter"], cor, ocr)  # 选择队伍
        BlackFlowActive.select_ticket(templates["team_enter"], ocr, '稳扎稳打')  # 选择招募组合
        # button_dict = BlackFlowActive.match_recruit_buttons(ocr)  # 获取招募券界面招募名称与对应坐标
        # print(button_dict)
        button_dict = {'重装招募券': (526, 779), '术师招募券': (960, 779), '狙击招募券': (1394, 779)}
        for name, cor in button_dict.items():
            if name == '重装招募券':
                BlackFlowActive.handle_heavy(cor, ocr)
            else:
                BlackFlowActive.handle_quit(cor, ocr, templates["team_quit"])

        img_origin = connect.screen_shot()
        flag_quit, cor = main_start.ocr_process(ocr, img_origin, '沉沦于树海')
        start_enter = targetMatch.find_center_coordinate(cor)
        active.click(start_enter[0], start_enter[1])  # 点击进入局内

        end_flag = False
        while not end_flag:
            active.click(540, 100)  # 点击空白区域跳过
            img_origin = connect.screen_shot()
            end_flag, cor = main_start.ocr_process(ocr, img_origin, '险路尽头')
            time.sleep(1)

        # 2. --- 局内前进 ---
        print('装备移动工具')
        BlackFlowActive.wear_equipment(ocr, templates['map_check'])  # 装备移动工具
        img_origin = connect.screen_shot()
        _, cor_quit_enter = targetMatch.img_Match(templates['map_lower'], img_origin)
        print('点击缩小')
        active.click(cor_quit_enter[0], cor_quit_enter[1])  # 点击缩小
        time.sleep(2)  # 等待缩小完毕

        ocr_manager.force_restart()
        ocr = ocr_manager.get_ocr()

        # 3. --- 事件行为 ---
        print('开始事件')
        BlackFlowActive.handle_rogue_graph(ocr, templates['event_exit'], templates['map_check'], '诡意行商')

        # 4. --- 退出游戏 ---
        print('退出游戏')
        BlackFlowActive.exit_game(templates['exit'], templates['game_quit'], templates['epoch_end_enter'],
                                  ocr, height, width)

        time_end = time.time()

        print('一轮用时', time_end - time_start)
    except Exception as e:
        print('程序异常终止，全部退出', e)
        sys.exit(0)


if __name__ == '__main__':
    ocr1 = PaddleOCR(use_angle_cls=True, lang='ch')
    ocr_manager = OCRManager()

    templates1 = load_all_templates()

    connect.end_connect()
    print('开始连接')
    connect.connect_mumu_emulator(16384)
    print('截图测试')
    img1 = connect.screen_shot_local('rogue/aaa.png')
    height, width = img1.shape[:2]

    del img1
    gc.collect()

    # BlackFlowActive.mystery_store(ocr1)
    # sys.exit(0)

    for i in range(EPOCH):
        print(f'\n第 {i + 1} 轮 | 当前时间: {time.strftime("%H:%M:%S")}')

        main_loop(ocr_manager, templates1, height, width, max_rounds=1)
        gc.collect()

    connect.end_connect()

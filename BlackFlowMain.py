"""
@File  ：BlackFlowMain.py
@Python：3.10
@Author：我的小熊掉了
@Date  ：2026/7/20 10:36

本程序为集成战略主题<沉沦者的黑流树海> 源石锭刷取脚本 v3.06
v1.0 主线关卡刷取脚本，自动使用理智道具
v2.0 添加界园主题源石锭刷取（由于界园dlc更新，节点修改，简易刷取方法失效）
v3.0 添加黑流树海主题源石锭刷取，采用机械师快速移动定位商店存款

v3.1 修改招募组合确认问题；修改招募干员招募失败问题；修改地图主界面识别错误问题
v3.3 修改部分节点事件判定错误问题；添加<险路小径>节点判定
v3.4 修改不期而遇事件处理问题，添加不期而遇事件
v3.5 修改存款时携带源石锭不足的问题
v3.6 修改招募券滑动失败问题
v3.6 优化装备穿戴逻辑，避免无意义卡顿；修改坐标设置错误问题

# 要求:
# 模拟器分辨率设置为1920*1080;模拟器连接端口16384


使用方法：
1.刷取主线/活动关卡：
运行main_start.py；{param:level, min_day_threshold, max_total_use}
设置关卡名称level:str；默认'1 - 7'
设置min_day_threshold & max_total_use；
优先使用小于min_day_threshold的所有道具；
若道具剩余时间充足，则设置max_total_use限制最大使用数量；

2.<集成战略主题：沉沦者的黑流树海>源石锭存款
运行BlackFlowMain.py；{param:EPOCH}
设置运行轮次EPOCH，默认EPOCH=100
"""

import os
import subprocess
import time
import logging

logging.disable(logging.DEBUG)  # 关闭DEBUG日志的打印
logging.disable(logging.WARNING)  # 关闭WARNING日志的打印
os.environ['FLAGS_allocator_strategy'] = 'naive_best_fit'

import sys

sys.path.append('./my_utils')
import gc

from memory_profiler import profile
import cv2
import numpy as np
from paddleocr import PaddleOCR
import difflib
from collections import deque

import main_start
from my_utils import targetMatch
from my_utils import active
from my_utils import connect
import jieGarden_active
import BlackFlowActive


EPOCH = 100  # 循环轮数


def load_all_templates():
    """统一加载模板图像，避免重复读取"""
    return {
        "team_enter": cv2.imread('rogue_blackflow/team_enter.png', 0),
        "team_quit": cv2.imread('rogue_blackflow/quit_enter.png', 0),
        "map_lower": cv2.imread('rogue_blackflow/litter.png', 0),
        "event_exit": cv2.imread('rogue_blackflow/event_quit.png', 0),
        "exit": cv2.imread('rogue_blackflow/exit.png', 0),
        "game_quit": cv2.imread('rogue_blackflow/quit_enter.png', 0),
        "epoch_end_enter": cv2.imread('rogue_blackflow/game_over.png', 0)
    }


def main_loop(ocr, templates, height, width, max_rounds=100):
    """
    :param ocr: ocr模型
    :param templates: load_all_templates()加载的图片
    :param height: 模拟器分辨率 高
    :param width: 模拟器分辨率 宽
    :param max_rounds: 最大循环次数
    :return: None
    """
    for cnt in range(max_rounds):

        time_start = time.time()
        try:
            # 1. --- 进入本局 ---
            cor = BlackFlowActive.start(ocr, '开始探索', '堡垒战术分队')  # 开始探索
            jieGarden_active.select_team(templates["team_enter"], cor, ocr)  # 选择队伍
            BlackFlowActive.select_ticket(templates["team_enter"], ocr, '稳扎稳打')  # 选择招募组合
            button_dict = BlackFlowActive.match_recruit_buttons(ocr)
            print(button_dict)
            for name, cor in button_dict.items():
                if name == '重装招募券':
                    BlackFlowActive.handle_heavy(cor, ocr)
                else:
                    BlackFlowActive.handle_quit(cor, ocr, templates["team_quit"])

            img_origin = connect.screen_shot(r'rogue/aaa.png')
            flag_quit, cor = main_start.ocr_process(ocr, img_origin, '沉沦于树海')
            start_enter = targetMatch.find_center_coordinate(cor)
            active.click(start_enter[0], start_enter[1])  # 点击进入局内

            end_flag = False
            while not end_flag:
                active.click(540, 100)  # 点击空白区域跳过
                img_origin = connect.screen_shot(r'rogue/aaa.png')
                end_flag, cor = main_start.ocr_process(ocr, img_origin, '险路尽头')
                time.sleep(1)

            # 2. --- 局内前进 ---
            print('装备移动工具')
            BlackFlowActive.wear_equipment(ocr)  # 装备移动工具
            img_origin = connect.screen_shot(r'rogue/aaa.png')
            _, cor_quit_enter = targetMatch.img_Match(templates['map_lower'], img_origin)
            print('点击缩小')
            active.click(cor_quit_enter[0], cor_quit_enter[1])  # 点击缩小
            time.sleep(2)  # 等待缩小完毕

            # 3. --- 事件行为 ---
            print('开始事件')
            BlackFlowActive.handle_rogue_graph(ocr, templates['event_exit'], '诡意行商')

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
    sys.dont_write_bytecode = True

    ocr1 = PaddleOCR(use_angle_cls=True, lang='ch')
    templates1 = load_all_templates()

    connect.connect_mumu_emulator(16384)
    img1 = connect.screen_shot()
    height, width = img1.shape[:2]

    # BlackFlowActive.path_end(templates1['event_exit'], ocr1)

    for i in range(EPOCH):
        print(f'\n第 {i + 1} 轮 | 当前时间: {time.strftime("%H:%M:%S")}')
        main_loop(ocr1, templates1, height, width, max_rounds=1)

        os.system('cls')
        gc.collect()
    connect.end_connect()

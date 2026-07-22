"""
@File  ：BlackFlowActive.py
@Python：3.10
@Author：我的小熊掉了
@Date  ：2026/7/20 10:29 
"""
import math
import time
import gc

import main_start
import rogue_test
import logging

logging.disable(logging.DEBUG)  # 关闭DEBUG日志的打印
logging.disable(logging.WARNING)  # 关闭WARNING日志的打印

import sys

sys.path.append('./my_utils')

import cv2
import numpy as np
from paddleocr import PaddleOCR
from my_utils import targetMatch
from my_utils import active
from my_utils import connect
import jieGarden_active


FOOT_EQUIPMENT_COORD = [1720, 150]  # 行动力坐标
BLANK_AREA_COORD_MAP = [100, 540]  # 地图空白区域坐标
BLANK_AREA_COORD_EVENT = [1000, 50]  # 事件空白区域坐标
EVENT_COORD_BIAS = [100, 50]  # 事件点击坐标偏置
ENTER_COORD_BIAS = [0, 30]  # 事件确认坐标偏置


def normal_slide():
    """
    手势为向左滑动屏幕，寻找右边的分队，分辨率1920*1080
    :return:
    """
    active.slide_press(1536, 540, 784, 540, 2000)
    time.sleep(2)


def character_slide():
    """
    手势为向左滑动屏幕，寻找右边的分队，分辨率1920*1080
    :return:
    """
    active.slide_press(1720, 540, 1000, 540, 2000)
    time.sleep(2)


def start(ocr, menu, team, slide_team=True):
    """
    :param ocr: ocr模型
    :param menu: str类型, 设置开始游戏识别文字，如“开始探索”
    :param team: str类型，设置分队名字，如“指挥分队”
    :param slide_team: bool类型，设置目标分队是否需要滑动寻找
    :return: 返回 “<指挥分队>” 坐标 [x, y] 下一步进行分队选择
    """
    flag = True

    while flag:
        flag1 = False
        if flag1:
            break

        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag, cor0 = main_start.ocr_process(ocr, img_origin, menu)  # 主界面寻找开始位置
        cor0 = targetMatch.find_center_coordinate(cor0)
        active.click(cor0[0], cor0[1])  # 主界面寻找开始
        time.sleep(1)  # 等待进入分队选择

        while not flag1:
            img_origin = connect.screen_shot(r'rogue/aaa.png')
            flag1, _ = main_start.ocr_process(ocr, img_origin, '选择分队')

    if slide_team:  # 滑动界面
        normal_slide()  # 滑动寻找目标分队
        time.sleep(1.5)  # 等待滑动惯性

    flag = False  # 设置跳转标志位
    cor1 = [0, 0]
    while not flag:
        select_team_img = connect.screen_shot(r'rogue/aaa.png')  # 截图
        print('寻找目标分队')
        flag, cor1 = main_start.ocr_process(ocr, select_team_img, team)  # 寻找分队，设置标志位，储存坐标
        time.sleep(0.5)
    cor1 = targetMatch.find_center_coordinate(cor1)
    time.sleep(0.5)

    del img_origin
    gc.collect()

    return cor1


def select_ticket(enter_img, ocr, tick_name):
    """
    :param enter_img: 图片rogue/team_enter.png
    :param ocr: OCR文字识别模型
    :param tick_name: 招募券组合的种类, 例如:<稳扎稳打>、<先手必胜>
    :return: None 下一步进行招募券花费
    """
    print(f'寻找<{tick_name}>组合')
    flag = False
    while not flag:
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag, _ = main_start.ocr_process(ocr, img_origin, '你确定要这么做')  # 保证有对号后退出
        if flag:
            break

        flag_ticket, cor0 = main_start.ocr_process(ocr, img_origin, tick_name)  # 组合名称寻找开始
        if flag_ticket:
            print(f'点击<{tick_name}>组合')
            cor0 = targetMatch.find_center_coordinate(cor0)  # 找到中心点
            active.click(cor0[0], cor0[1])  # 点击确认组合
        time.sleep(1)

    flag = False
    while not flag:
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag, _ = main_start.ocr_process(ocr, img_origin, '初始招募')  # 保证有对号后退出
        if flag:
            break

        print('匹配确认按钮')
        flag, cor0 = targetMatch.img_Match(enter_img, img_origin)
        if flag:
            print('点击招募组合确认')
            active.click(cor0[0], cor0[1])  # 点击确认招募券组合
            time.sleep(1)
        else:
            print('未找到招募券确认按钮')


def match_recruit_buttons(creat_ocr):
    """
    匹配招募位置坐标
    :param creat_ocr: OCR模型
    :param img: 要识别的图片
    :return: 字典 {'招募券名称': [按钮中心x, 按钮中心y], ...}
    """
    img = connect.screen_shot(r'rogue/aaa.png')

    word = creat_ocr.ocr(img, cls=True)

    # 收集所有识别到的招募券名称及其坐标
    recruit_cards = []
    if word and word[0] is not None:
        for line in word[0]:
            text = line[1][0]
            coords = line[0]
            if '招募券' in text:
                center = targetMatch.find_center_coordinate(coords)
                recruit_cards.append({
                    'name': text,
                    'center': center,
                    'coords': coords
                })

    # 如果没有识别到任何招募券，返回空字典
    if not recruit_cards:
        return {}

    # 收集所有"招募"按钮的坐标
    recruit_buttons = []
    if word and word[0] is not None:
        for line in word[0]:
            text = line[1][0]
            coords = line[0]
            if text == '招募':
                center = targetMatch.find_center_coordinate(coords)
                recruit_buttons.append(center)

    # 如果没有识别到任何"招募"按钮，返回空字典
    if not recruit_buttons:
        return {}

    # 为每个招募券匹配最近的"招募"按钮
    result = {}
    for card in recruit_cards:
        card_center = card['center']
        min_distance = float('inf')
        closest_button = None

        for button_center in recruit_buttons:
            # 计算欧几里得距离
            distance = ((card_center[0] - button_center[0]) ** 2 +
                        (card_center[1] - button_center[1]) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_button = button_center

        if closest_button:
            result[card['name']] = closest_button

    return result


def handle_heavy(recruit_cor, ocr_model):
    """重装招募任务"""
    print('执行重装招募任务')
    active.click(recruit_cor[0], recruit_cor[1])  # 点击确认招募券
    flag = False  # 检查是否进入干员选择界面
    while not flag:
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag, cor = main_start.ocr_process(ocr_model, img_origin, '选择助战')
        if flag:
            break
        time.sleep(2)

    print('向右滑动')
    character_slide()

    img_origin = connect.screen_shot(r'rogue/aaa.png')
    flag, cor = main_start.ocr_process(ocr_model, img_origin, '机械师')
    center = targetMatch.find_center_coordinate(cor)
    active.click(center[0]-30, center[1]-20)  # 点击干员
    time.sleep(0.5)

    flag, cor2 = main_start.ocr_process(ocr_model, img_origin, '确认招募')  # 招募干员
    center2 = targetMatch.find_center_coordinate(cor2)
    active.click(center2[0], center2[1])
    time.sleep(0.5)

    button_flag = False
    while not button_flag:  # 返回招募界面
        active.click(BLANK_AREA_COORD_MAP[0], BLANK_AREA_COORD_MAP[1])  # 点击空白区域跳过
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        print('查找是否退出到招募券界面')
        button_flag, cor = main_start.ocr_process(ocr_model, img_origin, '初始招募')
        time.sleep(0.5)


def handle_quit(recruit_cor, ocr_model, quit_img):
    """默认招募任务"""
    print('执行放弃招募任务')
    flag_quit = False
    while not flag_quit:  # 等待选择干员界面
        active.click(recruit_cor[0], recruit_cor[1])  # 点击确认招募券
        img_origin = connect.screen_shot(r'rogue/aaa.png')  # 继续寻找
        print('查找是否进入招募界面')
        flag_quit, cor_quit = main_start.ocr_process(ocr_model, img_origin, '放弃')  # 寻找放弃按钮
        if flag_quit:
            break
        time.sleep(1)
    cor_quit = targetMatch.find_center_coordinate(cor_quit)
    print('点击放弃招募')
    active.click(cor_quit[0], cor_quit[1])  # 点击放弃招募券
    time.sleep(2)  # 等待弹出确认框
    img_origin = connect.screen_shot(r'rogue/aaa.png')
    print('开始寻找放弃确认按钮')
    _, cor_quit_enter = targetMatch.img_Match(quit_img, img_origin)  # 匹配**********************
    active.click(cor_quit_enter[0], cor_quit_enter[1])  # 点击放弃招募券

    button_flag = False
    while not button_flag:  # 返回招募界面
        time.sleep(1)
        active.click(BLANK_AREA_COORD_MAP[0], BLANK_AREA_COORD_MAP[1])  # 点击空白区域跳过
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        print('查找是否退出到招募券界面')
        button_flag, cor = main_start.ocr_process(ocr_model, img_origin, '初始招募')

    return cor_quit, cor_quit_enter


def wear_equipment(ocr):
    """
    装备移动工具
    :param ocr: 文字识别模块
    :return: None
    """

    # 点击道具列表
    active.click(FOOT_EQUIPMENT_COORD[0], FOOT_EQUIPMENT_COORD[1])
    time.sleep(1)

    flag = False  # 结构性原理标志位
    while not flag:
        print('点击行动力道具')
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag, cor = main_start.ocr_process(ocr, img_origin, '结构性原理')
        if flag:
            center = targetMatch.find_center_coordinate(cor)
            active.click(center[0], center[1])  # 点击结构性原理装备
            break

        time.sleep(1)

    active.click(BLANK_AREA_COORD_MAP[0], BLANK_AREA_COORD_MAP[1])  # 点击空白区域跳过，退出到地图主界面
    flag = False
    while not flag:
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag, cor = main_start.ocr_process(ocr, img_origin, '行动力')
        time.sleep(1)

    time.sleep(1)


def find_nearest_node(creat_ocr, img, target_nodes, exclude_nodes=None):
    """
    在地图中寻找距离<险路尽头>最近的指定类型节点
    :param creat_ocr: OCR模型
    :param img: 截图图片
    :param target_nodes: 目标节点名称列表 ['诡意行商', '未知的诡秘']
    :param exclude_nodes: 排除的节点坐标列表，用于避免重复进入同一个节点
    :return: (节点名称, 节点中心坐标) 或 (None, None)
    """
    word = creat_ocr.ocr(img, cls=True)

    # 收集所有节点
    nodes = []
    for line in word[0]:
        text = line[1][0]
        coords = line[0]
        # 检查是否为目标节点
        for target in target_nodes:
            if target in text:
                center = targetMatch.find_center_coordinate(coords)
                nodes.append({
                    'name': target,
                    'text': text,
                    'center': center,
                    'coords': coords
                })
                break

    # 如果没有节点，返回空
    if not nodes:
        return None, None

    # 寻找<险路尽头>的位置
    danger_end = None
    for line in word[0]:
        text = line[1][0]
        if '险路尽头' in text:
            danger_end = targetMatch.find_center_coordinate(line[0])
            break

    if danger_end is None:
        return None, None

    # 排除已进入的节点
    if exclude_nodes:
        nodes = [n for n in nodes if n['center'] not in exclude_nodes]
        if not nodes:
            return None, None

    # 计算距离，优先诡意行商
    target_nodes_priority = ['诡意行商', '未知的诡秘']

    # 先找诡意行商
    for priority in target_nodes_priority:
        priority_nodes = [n for n in nodes if n['name'] == priority]
        if priority_nodes:
            # 找距离最近的
            min_node = None
            min_dist = float('inf')
            for node in priority_nodes:
                dist = math.sqrt((node['center'][0] - danger_end[0]) ** 2 +
                                 (node['center'][1] - danger_end[1]) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    min_node = node
            if min_node:
                return min_node['text'], min_node['center']

    return None, None


def handle_rogue_graph(creat_ocr, event_quit_img, target_node_type='诡意行商'):
    """
    处理肉鸽地图节点选择
    :param creat_ocr: OCR模型
    :param event_quit_img: 事件退出图片 event_quit.png
    :param target_node_type: 目标节点类型 '诡意行商' 或 '未知的诡秘'
    :return: None
    """
    visited_nodes = []  # 记录已进入的节点坐标

    while True:
        # 截图
        img = connect.screen_shot(r'rogue/aaa.png')

        # 优先找诡意行商，如果没有则找未知的诡秘
        target_list = ['诡意行商', '未知的诡秘']
        node_name, node_center = find_nearest_node(
            creat_ocr,
            img,
            target_list,
            visited_nodes
        )

        if node_center is None:
            print('未找到目标节点')
            break

        print(f'找到节点: {node_name}，坐标: {node_center}')

        active.click(node_center[0], node_center[1])  # 点击节点
        time.sleep(1)

        img_origin = connect.screen_shot(r'rogue/aaa.png')
        node_flag, cor = main_start.ocr_process(creat_ocr, img_origin, '出发前往')
        center = targetMatch.find_center_coordinate(cor)
        active.click(center[0], center[1])  # 点击出发

        leave_flag = False
        while not leave_flag:
            active.click(BLANK_AREA_COORD_MAP[0], BLANK_AREA_COORD_MAP[1])  # 点击空白区域跳过
            img_origin = connect.screen_shot(r'rogue/aaa.png')
            leave_flag, cor = main_start.ocr_process(creat_ocr, img_origin, '玻利瓦尔肤层')
            time.sleep(1)
        time.sleep(1)

        # 诡意行商：1   秘境行商：2  不期而遇：3  先行一步：
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        event_flag1, _ = main_start.ocr_process(creat_ocr, img_origin, '前瞻性投资系统')  # 诡意行商
        event_flag2, _ = main_start.ocr_process(creat_ocr, img_origin, '开始培育')  # 秘境行商
        event_flag3, _ = main_start.ocr_process(creat_ocr, img_origin, '无人商店')  # 得偿所愿
        event_flag4, _ = main_start.ocr_process(creat_ocr, img_origin, '离开黑池')  # 险路尽头
        event_flag5, _ = main_start.ocr_process(creat_ocr, img_origin, '三重身')  # 险路小径
        # 先行一步↑ ###

        if event_flag1:
            event_state = 1  # 诡意行商
        elif event_flag2:
            event_state = 2  # 秘境行商  点击离开
        elif event_flag3:
            event_state = 3  # 得偿所愿  点击中间退出
        elif event_flag4 or event_flag5:
            event_state = 4  # 险路尽头  使用event_quit.png退出
        else:
            print('没有识别到关卡')
            event_state = 5  # 不期而遇

        print('进入的事件是', event_state)

        if event_state == 1:
            # 处理诡意行商
            handle_gu_yi_event(creat_ocr)
            break  # 完成诡意行商后退出
        else:
            handle_other_event(creat_ocr, event_state, event_quit_img)
            continue


def handle_gu_yi_event(creat_ocr):
    """
    处理诡意行商事件
    """
    print('进入诡意行商')
    # TODO: 编写诡意行商事件处理逻辑
    print('点击当前余额')
    flag = False
    while not flag:
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag, cor = main_start.ocr_process(creat_ocr, img_origin, '当前余额')
        del img_origin
        gc.collect()
        time.sleep(1)
    cor = targetMatch.find_center_coordinate(cor)
    active.click(cor[0], cor[1])
    time.sleep(1)

    print('点击投资入口')
    img_origin = connect.screen_shot(r'rogue/aaa.png')
    _, cor = main_start.ocr_process(creat_ocr, img_origin, '投资入口')
    del img_origin
    gc.collect()
    cor = targetMatch.find_center_coordinate(cor)
    active.click(cor[0], cor[1])
    time.sleep(1)

    print('点击确认投资')
    img_origin = connect.screen_shot(r'rogue/aaa.png')
    _, cor = main_start.ocr_process(creat_ocr, img_origin, '确认投资')
    del img_origin
    gc.collect()
    cor = targetMatch.find_center_coordinate(cor)

    flag = False
    while not flag:
        active.click(cor[0], cor[1])
        time.sleep(0.5)
        active.click(cor[0], cor[1])
        time.sleep(0.5)
        active.click(cor[0], cor[1])
        time.sleep(0.8)
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag1, _ = main_start.ocr_process(creat_ocr, img_origin, '投资受限')
        flag2, _ = main_start.ocr_process(creat_ocr, img_origin, '源石锭不足')
        if flag1:
            print('投资受限')
        elif flag2:
            print('源石锭不足')
        flag = flag1 or flag2

        del img_origin
        gc.collect()

    print('投资完成')


def handle_other_event(creat_ocr, event_state, event_quit_img):
    """
    处理其他事件（秘境行商、不期而遇等）
    """
    print('进入其他事件')
    # TODO: 编写其他事件处理逻辑
    time.sleep(1)
    if event_state == 2:
        print('秘境行商')
        mystery_store(creat_ocr)

    if event_state == 3:
        print('得偿所愿')
        achievement(creat_ocr)

    if event_state == 4:
        print('险路尽头 或 险路小径')
        path_end(event_quit_img, creat_ocr)

    if event_state == 5:
        print('不期而遇')
        event(event_quit_img, creat_ocr)


def mystery_store(ocr):
    img_origin = connect.screen_shot(r'rogue/aaa.png')
    _, cor0 = main_start.ocr_process(ocr, img_origin, '离开')
    cor0 = targetMatch.find_center_coordinate(cor0)
    active.click(cor0[0], cor0[1])
    time.sleep(1)

    img_origin = connect.screen_shot(r'rogue/aaa.png')
    _, cor0 = main_start.ocr_process(ocr, img_origin, '确认离开')
    cor0 = targetMatch.find_center_coordinate(cor0)
    active.click(cor0[0], cor0[1])
    time.sleep(1)

    flag = False
    while not flag:
        print('查看是否返回地图')
        active.click(BLANK_AREA_COORD_EVENT[0], BLANK_AREA_COORD_EVENT[1])
        flag, cor0 = main_start.ocr_process(ocr, img_origin, '行动力')
        time.sleep(1)


def achievement(ocr):
    flag1 = False
    while not flag1:
        active.click(1440, 540)
        time.sleep(1)
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag1, cor0 = main_start.ocr_process(ocr, img_origin, '你确定要这么做')
        if flag1:
            cor0 = targetMatch.find_center_coordinate(cor0)
            active.click(cor0[0], cor0[1])
            break

    flag = False
    while not flag:
        print('查看是否返回地图')
        active.click(BLANK_AREA_COORD_EVENT[0], BLANK_AREA_COORD_EVENT[1])
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        flag, cor0 = main_start.ocr_process(ocr, img_origin, '行动力')
        if flag:
            break
        time.sleep(1)


def path_end(event_quit_img, ocr):
    """
    :param event_quit_img:  event_quit.png
    :param ocr: 文字识别ocr
    :return:  None
    """
    img_origin = connect.screen_shot(r'rogue/aaa.png')
    flag, cor = targetMatch.img_Match(event_quit_img, img_origin)
    active.click(cor[0], cor[1])
    time.sleep(1)

    img_origin = connect.screen_shot(r'rogue/aaa.png')
    _, cor0 = main_start.ocr_process(ocr, img_origin, '确定这么做')
    cor0 = targetMatch.find_center_coordinate(cor0)
    active.click(cor0[0], cor0[1]+20)

    flag = False
    while not flag:
        print('查看是否返回地图')
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        active.click(BLANK_AREA_COORD_EVENT[0], BLANK_AREA_COORD_EVENT[1])
        flag, cor0 = main_start.ocr_process(ocr, img_origin, '行动力')
        if flag:
            break
        time.sleep(1)


def event(event_quit_img, ocr):
    """
    :param event_quit_img:  event_quit.png
    :param ocr: 文字识别ocr
    :return: None
    """
    # 不期而遇事件字典，键key位为事件名称，值value为选项名称
    event_list = {'桑尼的邀请': '唱一首摇篮曲',
                  '沉寂之屋': '离开',
                  '思乡心切': '多一事不如少一事'
                  }

    img_origin = connect.screen_shot(r'rogue/aaa.png')
    flag1, cor1 = main_start.ocr_process(ocr, img_origin, '多一事不如少一事')
    flag2, cor2 = main_start.ocr_process(ocr, img_origin, '离开')
    flag3, cor3 = main_start.ocr_process(ocr, img_origin, '唱一首摇篮曲')

    if flag1 or flag2:
        print('直接离开事件')
        f, center = targetMatch.img_Match(event_quit_img, img_origin)
        active.click(center[0], center[1])
        time.sleep(1)
    elif flag3:
        print('奖励事件')
        center = targetMatch.find_center_coordinate(cor1)
        active.click(center[0] + 100, center[1] + 50)

    # 退出事件
    img_origin = connect.screen_shot(r'rogue/aaa.png')
    _, cor0 = main_start.ocr_process(ocr, img_origin, '确定这么做')
    cor0 = targetMatch.find_center_coordinate(cor0)
    active.click(cor0[0], cor0[1] + 20)

    flag = False
    while not flag:
        print('查看是否返回地图')
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        active.click(BLANK_AREA_COORD_EVENT[0], BLANK_AREA_COORD_EVENT[1])
        flag, cor0 = main_start.ocr_process(ocr, img_origin, '行动力')
        if flag:
            break
        time.sleep(1)


def exit_game(img_exit, img_quit_enter, img_game_over, ocr, height, width):
    """
    :param img_exit:  exit.png
    :param img_quit_enter:  quit_enter.png
    :param img_game_over:  team_enter.png
    :param ocr:  文字识别ocr
    :param height: 高
    :param width: 宽
    :return: None
    """
    img_origin = connect.screen_shot(r'rogue/aaa.png')
    flag, cor = targetMatch.img_Match(img_exit, img_origin)
    active.click(cor[0], cor[1])
    time.sleep(1)

    img_origin = connect.screen_shot(r'rogue/aaa.png')
    _, cor0 = main_start.ocr_process(ocr, img_origin, '放弃本次探索')
    cor0 = targetMatch.find_center_coordinate(cor0)
    active.click(cor0[0], cor0[1])
    time.sleep(1)

    img_origin = connect.screen_shot(r'rogue/aaa.png')
    flag, cor = targetMatch.img_Match(img_quit_enter, img_origin)
    active.click(cor[0], cor[1])
    time.sleep(1)

    while True:
        # 截图
        img_origin = connect.screen_shot(r'rogue/aaa.png')
        active.click(int(height / 2), int(width / 2))
        time.sleep(1)

        # 寻找"开始探索"
        print('寻找"开始探索"')
        flag, cor0 = main_start.ocr_process(ocr, img_origin, '开始探索')
        if flag:
            time.sleep(1)
            print('找到开始探索，结束')
            break

        # 没有找到"开始探索"，进行图片匹配
        print('寻找"结算对号"')
        match_flag, match_pos = targetMatch.img_Match(img_game_over, img_origin)
        if match_flag:
            print('匹配到结算对号')
            active.click(match_pos[0], match_pos[1])
            time.sleep(1)

        # 没有找到"开始探索"，进行机械师升级检测
        print('寻找"人物升级"')
        flag1, cor1 = main_start.ocr_process(ocr, img_origin, '点击继续')
        if flag1:
            print('匹配到人物升级')
            cor1_center = targetMatch.find_center_coordinate(cor1)
            active.click(cor1_center[0], cor1_center[1])


"""=============================地图逻辑处理部分↑============================="""

# 不期而遇退出后需要循环查找【行动力】，网不好容易卡住
# 得偿所愿 点击【1440, 540】 点击确定这么做 {网不好容易卡住} 点击左边 {网不好容易卡住} 循环查找【险路尽头】

# 退出本局逻辑 == 点击中心 == 寻找”开始探索“ 有 ==停止 time.sleep(1.5) 开始下一轮
# 没有 == 判断图片匹配 == 有匹配 =点击图片位置
# 没有匹配 == 重复第一步

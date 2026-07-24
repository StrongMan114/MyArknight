"""
-*- coding: utf-8 -*-

@File: jieGarden_active.py
@author: 我的小熊掉了
@time: 2025/7/17 9:39
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


def start(ocr, menu='开始', team='指挥分队'):
    """
    :param ocr: ocr模型
    :param menu: str类型, 设置开始游戏识别文字，如“开始探索”
    :param team: str类型，设置分队名字，如“指挥分队”
    :return: 返回 “<指挥分队>” 坐标 [x, y] 下一步进行分队选择
    """
    img_origin = connect.screen_shot()

    flag, cor0 = main_start.ocr_process(ocr, img_origin, menu)  # 主界面寻找开始
    if flag:
        cor0 = targetMatch.find_center_coordinate(cor0)
        active.click(cor0[0], cor0[1])  # 主界面寻找开始
        time.sleep(1)  # 等待

    flag = False  # 设置跳转标志位
    cor1 = [0, 0]
    while not flag:
        select_team_img = connect.screen_shot(r'rogue/aaa.png')  # 截图
        print('寻找指挥分队')
        flag, cor1 = main_start.ocr_process(ocr, select_team_img, team)  # 寻找到指挥分队，设置标志位，储存坐标
        time.sleep(0.5)
    cor1 = targetMatch.find_center_coordinate(cor1)
    time.sleep(0.5)

    del img_origin
    gc.collect()

    return cor1


def select_team(enter_img, cor, ocr):
    """
    :param enter_img: 图片rogue/team_enter.png
    :param cor: 指挥分队的坐标，由流程中start()方法返回
    :return: None 下一步进行干员组合选择
    """
    active.click(cor[0], cor[1])  # 选择分队
    time.sleep(2)
    flag = True

    while flag:
        flag1 = False
        if flag1:
            break

        img_origin = connect.screen_shot()
        flag, cor0 = main_start.ocr_process(ocr, img_origin, '你确定要这么做')
        if flag:
            cor0 = targetMatch.find_center_coordinate(cor0)
            active.click(cor0[0], cor0[1])
        time.sleep(1)

        while not flag1:
            img_origin = connect.screen_shot()
            flag1, _ = main_start.ocr_process(ocr, img_origin, '选择招募组合')

    del img_origin
    gc.collect()


def select_ticket(enter_img, ocr):
    """
    :param enter_img: 图片rogue/team_enter.png
    :param ocr: OCR文字识别模型
    :return: None 下一步进行招募券花费
    """
    img_origin = connect.screen_shot()
    print('寻找<先手必胜>组合')
    flag, cor0 = main_start.ocr_process(ocr, img_origin, '先手必胜')  # 主界面寻找开始
    if flag:
        print('点击<先手必胜>组合')
        cor0 = targetMatch.find_center_coordinate(cor0)  # 找到中心点
        active.click(cor0[0], cor0[1])  # 点击确认先手必胜
        time.sleep(2)
    else:
        print('未识别到招募券组合')

    img_origin = connect.screen_shot()
    print('寻找对号')
    flag, cor0 = targetMatch.img_Match(enter_img, img_origin)
    if flag:
        active.click(cor0[0], cor0[1])  # 点击确认招募券组合
        time.sleep(2)
    else:
        print('未找到招募券确认按钮')

    del img_origin
    gc.collect()


def select_character_quit(cor0, quit_img, ocr):
    # cor_quit最底边放弃坐标  cor_quit_enter放弃时对号的按钮坐标
    cor1 = cor0[0]
    active.click(cor1[0], cor1[1])  # 点击确认招募券
    time.sleep(1.8)
    img_origin = connect.screen_shot()
    flag_quit, cor_quit = main_start.ocr_process(ocr, img_origin, '放弃')  # 寻找放弃*************
    while not flag_quit:  # 等待选择干员界面
        img_origin = connect.screen_shot()  # 继续寻找
        flag_quit, cor_quit = main_start.ocr_process(ocr, img_origin, '放弃')  # 寻找放弃按钮******************
        time.sleep(1)
    cor_quit = targetMatch.find_center_coordinate(cor_quit)
    print('点击放弃招募')
    active.click(cor_quit[0], cor_quit[1])  # 点击放弃招募券
    time.sleep(2)  # 等待弹出确认框
    img_origin = connect.screen_shot()
    print('开始寻找放弃确认按钮')
    _, cor_quit_enter = targetMatch.img_Match(quit_img, img_origin)  # 匹配**********************
    active.click(cor_quit_enter[0], cor_quit_enter[1])  # 点击放弃招募券
    time.sleep(2)  # 等待放弃完毕

    return cor_quit, cor_quit_enter


def select_character(quit_img, tongbao_img, ocr):
    """
    :param quit_img: 放弃图片
    :param tongbao_img: 通宝图片
    :param ocr: OCR模型
    :return: None
    """
    img_origin = connect.screen_shot()
    print('选择完干员并进入')
    flag, cor0 = main_start.multi_ocr_process(ocr, img_origin, '招募')  # 寻找所有招募坐标
    if flag:
        cor_quit, cor_quit_enter = select_character_quit(cor0, quit_img, ocr)
        for i in range(len(cor0) - 1):
            cor1 = cor0[i + 1]
            active.click(cor1[0], cor1[1])
            time.sleep(1.8)
            img_origin = connect.screen_shot()
            flag_quit, _ = main_start.ocr_process(ocr, img_origin, '放弃')
            while not flag_quit:
                del img_origin
                gc.collect()

                img_origin = connect.screen_shot()
                flag_quit, _ = main_start.ocr_process(ocr, img_origin, '放弃')
                time.sleep(1)
            del img_origin
            gc.collect()

            active.click(cor_quit[0], cor_quit[1])
            time.sleep(2)
            active.click(cor_quit_enter[0], cor_quit_enter[1])
            time.sleep(2)
    time.sleep(1)  # 等待放弃完毕
    img_origin = connect.screen_shot()
    print('招募券全部放弃')
    flag_a, cor_enter_a = main_start.ocr_process(ocr, img_origin, '此')  # 寻找安全坐标
    flag_b, cor_enter_b = main_start.ocr_process(ocr, img_origin, '进')  # 寻找安全坐标
    if flag_a and flag_b:
        cor_enter_a = targetMatch.find_center_coordinate(cor_enter_a)
        cor_enter_b = targetMatch.find_center_coordinate(cor_enter_b)
        cor_quit = ((cor_enter_a[0] + cor_enter_b[0]) / 2, (cor_enter_a[1] + cor_enter_b[1]) / 2)
        active.click(cor_quit[0], cor_quit[1])  # 点击进入游戏
        time.sleep(7)  # 等待进入游戏
    else:
        print('没找到招募券选完后的进入按钮')

    print('等待投出通宝')
    flag_tongbao = False
    cor1 = [10, 10]
    while not flag_tongbao:
        img_origin = connect.screen_shot()  # 继续寻找
        try:
            flag1, cor1 = targetMatch.img_Match(tongbao_img, img_origin)  # 寻找放弃按钮
            flag2, _ = main_start.ocr_process(ocr, img_origin, '投出的通宝将在本层生效')  # 寻找放弃按钮
        except:
            flag1 = False
            flag2 = False
        if flag1 and flag2:
            print('投钱完毕')
            flag_tongbao = True
        time.sleep(1)  # 缓冲
    time.sleep(1)  # 缓冲
    print('进入关卡')
    active.click(cor1[0], cor1[1])  # 点击进入关卡选择
    time.sleep(1)  # 缓冲
    del img_origin
    gc.collect()


def battle_process(ocr, quit_img, setting_img, quit_battle_img):
    """
    :param ocr: ocr模型
    :param quit_img: quit_enter.png
    :param setting_img: setting.png
    :param quit_battle_img: quit_battle.png
    :return: None
    """
    img_origin = connect.screen_shot()
    flag, cor = main_start.ocr_process(ocr, img_origin, 'READYTO')
    del img_origin
    gc.collect()

    if flag:
        print('准备进入战斗关')
        cor = targetMatch.find_center_coordinate(cor)
        active.click(cor[0], cor[1])
        time.sleep(2)
    else:
        print('没有找到进入战斗的按钮')

    print('编队')
    img_origin = connect.screen_shot()
    _, cor = main_start.ocr_process(ocr, img_origin, '开始行动')
    del img_origin
    gc.collect()

    cor = targetMatch.find_center_coordinate(cor)
    active.click(cor[0], cor[1])
    time.sleep(1.5)

    print('点击确认编队')
    img_origin = connect.screen_shot()
    _, cor_quit_enter = targetMatch.img_Match(quit_img, img_origin)
    del img_origin
    gc.collect()
    active.click(cor_quit_enter[0], cor_quit_enter[1])

    print('点击设置')
    flag = False
    while not flag:
        img_origin = connect.screen_shot()
        try:
            flag, cor = targetMatch.img_Match(setting_img, img_origin)
        except:
            pass
        del img_origin
        gc.collect()
        time.sleep(1)
    active.click(cor[0], cor[1])
    time.sleep(1)

    print('点击放弃战斗')
    flag = False
    while not flag:
        img_origin = connect.screen_shot()
        try:
            flag, cor = targetMatch.img_Match(quit_battle_img, img_origin)
        except:
            pass
        del img_origin
        gc.collect()
        time.sleep(0.8)
    active.click(cor[0], cor[1])
    time.sleep(1)

    print('寻找放弃行动文字')
    flag = False
    while not flag:
        img_origin = connect.screen_shot()
        flag, cor = main_start.ocr_process(ocr, img_origin, '放弃行动')
        del img_origin
        gc.collect()
        time.sleep(1)
    cor = targetMatch.find_center_coordinate(cor)
    active.click(cor[0], cor[1])

    flag = False
    while not flag:
        img_origin = connect.screen_shot()
        flag, _ = main_start.ocr_process(ocr, img_origin, '目标生命值')
        if not flag:
            active.click(800, 200)
        del img_origin
        gc.collect()
        time.sleep(1)
    print('战斗结束')


def event_select(img):
    width, height = (1920, 1080)
    event_img1 = [{'偏安': 'rogue/event_money.png'},
                  ]
    event_img2 = [{'来者不拒': 'rogue/event_exit.png'},
                  {'饕餮郎': 'rogue/event_exit.png'},
                  {'护鸭金刚': 'rogue/event_exit.png'}
                  ]
    event_img3 = [{'岔路': 'rogue/event_exit.png'}]  # 需要滑动后识别
    active.slide(width * 0.85, height * 0.7, width * 0.85, height * 0.3)
    cata = 1  # 1:rogue/event_money.png ; 2:rogue/event_exit.png ; 3:active & 1 ; 4:active & 2
    if cata == 1:
        pass


def event_process(ocr, event_exit_img, event_money_img, event_exit_enter_img):
    """
    :param ocr:
    :param event_exit_img: rogue/event_exit.png
    :param event_money_img: rogue/event_money.png
    :param event_exit_enter_img: rogue/event_exit_enter.png
    :return:
    """
    img_origin = connect.screen_shot()
    height, width = img_origin.shape[:2]
    flag, cor = main_start.ocr_process(ocr, img_origin, 'READYTO')
    if flag:
        print('准备进入不期而遇')
        cor = targetMatch.find_center_coordinate(cor)
        active.click(cor[0], cor[1])  # 点击前往不期而遇
        time.sleep(3)  # 等待

    for i in range(3):
        active.click(800, 500)  # 点击前往不期而遇
        time.sleep(0.5)

    flag = False
    active.slide(width * 0.85, height * 0.7, width * 0.85, height * 0.35)
    time.sleep(1)  # 等待
    while not flag:
        active.click(200, 500)
        img_origin = connect.screen_shot()
        flag1, cor1 = targetMatch.img_Match(event_exit_img, img_origin)
        flag2, cor2 = targetMatch.img_Match(event_money_img, img_origin)
        if flag1 or flag2:
            flag = True
        time.sleep(1)  # 跳过对话
    if flag1:
        active.click(cor1[0], cor1[1])  # 点击退出
    elif not flag1 and flag2:
        active.click(cor2[0], cor2[1])  # 点击退出
    time.sleep(1)  # 等待

    flag = True
    while flag:
        img_origin = connect.screen_shot()
        flag, cor = targetMatch.img_Match(event_exit_enter_img, img_origin)
        if flag:
            active.click(cor[0], cor[1])  # 点击退出
        time.sleep(1)
        active.click(200, 500)  # 跳过对话
    time.sleep(1)

    flag = False  # 检测是否到地图节点界面
    while not flag:
        img_origin = connect.screen_shot()
        flag, _ = main_start.ocr_process(ocr, img_origin, '目标生命值')  # 检测是否到地图节点界面
        if not flag:
            active.click(200, 500)  # 随便点一下
        time.sleep(1)  # 缓冲
    print('结束不期而遇')
    del img_origin
    gc.collect()


def store_process(ocr):
    img_origin = connect.screen_shot()
    flag, cor = main_start.ocr_process(ocr, img_origin, 'READYTO')
    del img_origin
    gc.collect()

    if flag:
        print('准备进入诡意行商')
        cor = targetMatch.find_center_coordinate(cor)
        active.click(cor[0], cor[1])
        time.sleep(1)

    print('点击当前余额')
    flag = False
    while not flag:
        img_origin = connect.screen_shot()
        flag, cor = main_start.ocr_process(ocr, img_origin, '当前余额')
        del img_origin
        gc.collect()
        time.sleep(1)
    cor = targetMatch.find_center_coordinate(cor)
    active.click(cor[0], cor[1])
    time.sleep(1)

    print('点击投资入口')
    img_origin = connect.screen_shot()
    _, cor = main_start.ocr_process(ocr, img_origin, '投资入口')
    del img_origin
    gc.collect()
    cor = targetMatch.find_center_coordinate(cor)
    active.click(cor[0], cor[1])
    time.sleep(1)

    print('点击确认投资')
    img_origin = connect.screen_shot()
    _, cor = main_start.ocr_process(ocr, img_origin, '确认投资')
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
        img_origin = connect.screen_shot()
        flag, _ = main_start.ocr_process(ocr, img_origin, '投资受限')
        del img_origin
        gc.collect()

    print('投资完成')
    time.sleep(1)


def end_process(forward_flag, ocr, exit_img, quit_img, end_enter_img, is_activity_experience=True, is_mouth_task=True,
                is_character_experience=True):
    """
    :param forward_flag: 是否在地图节点中前进
    :param ocr:
    :param exit_img: rogue/exit.png
    :param quit_img: rogue/quit_enter.png
    :param end_enter_img: rogue/end_enter.png
    :param is_activity_experience: 经验结算后继续结算点击，游园纪念活动在时为True
    :param is_mouth_task: 游园纪念结算后若还有任务存在继续点击，每月活动在时为True
    :param is_character_experience: 干员升级活动在时，经验解算，为True
    :return: None
    """
    print('准备退出本局')
    img_origin = connect.screen_shot()
    _, cor = targetMatch.img_Match(exit_img, img_origin)
    active.click(cor[0], cor[1])  # 点击退出
    time.sleep(1)

    print('放弃探索')
    img_origin = connect.screen_shot()
    _, cor = main_start.ocr_process(ocr, img_origin, '放弃本次探索')
    cor = targetMatch.find_center_coordinate(cor)
    active.click(cor[0], cor[1])  # 放弃本次探索
    time.sleep(1)

    print('确认放弃探索')
    img_origin = connect.screen_shot()
    _, cor = targetMatch.img_Match(quit_img, img_origin)
    active.click(cor[0], cor[1])  # 点击放弃
    time.sleep(1)

    flag = False
    while not flag:
        active.click(800, 500)  # 点击放弃
        img_origin = connect.screen_shot()
        print('点击结束时的确认按钮')
        flag, cor = targetMatch.img_Match(end_enter_img, img_origin)  # 查找是否有白色对号
        time.sleep(1)
    active.click(cor[0], cor[1])  # 点击白色对号

    """第二次点击白色对号, 活动经验结算"""  ####################################
    if is_activity_experience:
        flag = False
        while not flag:
            img_origin = connect.screen_shot()
            flag, cor = targetMatch.img_Match(end_enter_img, img_origin)  # 等待白色对号
            time.sleep(1)
        active.click(cor[0], cor[1])  # 点击白色对号
        time.sleep(2)

    """每月委托，点击<空白区域>, 活动任务结算"""  ####################################
    if is_mouth_task:
        flag = False
        while not flag:
            img_origin = connect.screen_shot()
            flag, cor = main_start.ocr_process(ocr, img_origin, '进行中的本月委托')
            time.sleep(1.5)

        cor = targetMatch.find_center_coordinate(cor)
        active.click(cor[0], cor[1]-100)  # 点击<进行中的本月委托>
        time.sleep(3)

    """点击<点击继续>, 干员经验结算"""  ####################################
    if is_character_experience and forward_flag:
        flag = False
        cnt = 0
        while not flag:
            cnt = cnt + 1
            img_origin = connect.screen_shot()
            flag, cor = main_start.ocr_process(ocr, img_origin, '点击继续')
            time.sleep(1)

        cor = targetMatch.find_center_coordinate(cor)
        active.click(cor[0], cor[1])  # 点击继续
        time.sleep(1)

    flag = False
    while not flag:
        img_origin = connect.screen_shot()
        print('等待主界面')
        flag1, cor = main_start.ocr_process(ocr, img_origin, '点击继续')
        if flag1 and not flag:
            cor = targetMatch.find_center_coordinate(cor)
            active.click(cor[0], cor[1])  # 点击继续
        flag, _ = main_start.ocr_process(ocr, img_origin, '蚀刻章套组')  # 主界面寻找开始
        if flag:
            break
        time.sleep(0.5)

    print('本轮结束')
    del img_origin
    gc.collect()


def close_cor(cor_target, cor2_list):  # 最近坐标
    min_distance = math.inf
    cor = (0, 0)
    for i in cor2_list:
        d = math.sqrt(pow(abs(cor_target[0] - i[0]), 2) + pow(abs(cor_target[1] - i[1]), 2))
        if d < min_distance:
            min_distance = d
            cor = i
    return cor


def select_path(paths, level, num):
    """
    :param paths: 路径节点列表
    :param level: 关卡名称列表
    :param num: 节点序号
    :return: 1:战斗， 2:不期而遇， 3:诡意行商， 0:未有有效路径
            节点序号，节点名称，节点坐标
    """
    path = paths[0]
    path = sorted(path, key=lambda item: list(item.values()))  # 保证从左到右

    key = []
    value = []
    for i in range(len(path)):
        for x, y in path[i].items():
            key.append(x)
            value.append(y)

    if rogue_test.is_fuzzy_match(key[num], level, 0.6):
        return 1, key[num], value[num]
    elif key[num] == '不期而遇':
        return 2, key[num], value[num]
    elif key[num] == '诡意行商':
        return 3, key[num], value[num]
    else:
        return 0, None, (0, 0)


if __name__ == '__main__':
    level_name = ['x老戏骨', 'x狡鼷三窟', 'x赶集', 'x正经生意', 'x紧急作战']

    ocr1 = PaddleOCR(use_angle_cls=True, lang='ch')

    connect.connect_mumu_emulator(16384)  # 连接到模拟器

    tongbao_enter_img = cv2.imread('rogue/tongbao_enter.png', 0)
    team_quit_img = cv2.imread('rogue/quit_enter.png', 0)
    battle_setting_img = cv2.imread('rogue/setting.png', 0)
    battle_quit_img = cv2.imread('rogue/quit_battle.png', 0)
    event_exit_img = cv2.imread('rogue/event_exit.png', 0)
    event_money_img = cv2.imread('rogue/event_money.png', 0)
    event_exit_enter_img = cv2.imread('rogue/event_exit_enter.png', 0)
    exit_img = cv2.imread('rogue/exit.png', 0)
    epoch_end_enter = cv2.imread('rogue/end_enter.png', 0)

    # category, _, cor = select_path(paths, level_name, 1)
    # end_process(False, ocr1, exit_img, team_quit_img, epoch_end_enter, False, True)  # True验证,False验证
    # battle_process(ocr1, team_quit_img, battle_setting_img, battle_quit_img)  # 验证
    # event_process(ocr1, event_exit_img, event_money_img, event_exit_enter_img)  # 验证
    # store_process(ocr1)  # 验证

    connect.end_connect()  # 连接到模拟器

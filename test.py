"""
-*- coding: utf-8 -*-

@File: test.py
@author: 我的小熊掉了
@time: 2025/6/4 18:16
"""
import os
import sys

import main_start

sys.path.append('./my_utils')
from IPython.display import clear_output

import re
import time
import rogue_test
import jiegarden_money
from my_utils import active
from my_utils import connect
import BlackFlowActive
from my_utils.targetMatch import img_Match, find_center_coordinate, cv_show
import subprocess
import cv2
from paddleocr import PaddleOCR
from my_utils.package import arknights_bilibili, arknights_bilibili_activity, is_application_operation, \
    gracefully_close_arknights
import logging

logging.disable(logging.DEBUG)  # 关闭DEBUG日志的打印
logging.disable(logging.WARNING)  # 关闭WARNING日志的打印


def ocr_process(creat_ocr, img, word_target: str):
    word = creat_ocr.ocr(img, cls=True)  # [[[坐标],[坐标]...]，("识别文字",识别准确率)]

    coordinate = []

    for line in word[0]:
        # print(line[0], line[1][0], line[1][1])
        if word_target == line[1][0]:
            # print(line[0])
            return True, line[0]
    return False, coordinate


def multi_ocr_process(creat_ocr, img, word_target: str):
    word = creat_ocr.ocr(img, cls=True)  # [[[坐标],[坐标]...]，("识别文字",识别准确率)]

    coordinate = []

    for line in word[0]:
        if word_target == line[1][0]:
            a = find_center_coordinate(line[0])
            coordinate.append(a)

    if len(coordinate) > 0:
        return True, coordinate
    else:
        return False, coordinate


def extract_question_and_number(ocr_result, pattern):  # 判断使用理智还是
    """
    文字识别检测理智药使用情况
    return: tuple: (是否找到问题, 提取的数字) 如 (True, 160) 或 (False, None)
    """
    # 定义要匹配的问题模式（使用正则表达式）pattern

    # 遍历所有识别到的文本行
    for line in ocr_result:
        for word_info in line:
            text = word_info[1][0]  # 提取识别文本
            match = re.search(pattern, text)
            if match:
                # 提取数字并转换为整数
                number = int(match.group(1))  # match.group(0)是匹配的整体，match.group(1)为第一个括号里匹配的东西
                return True, number

    # 如果没有找到匹配
    return False, None


def extract_items_by_region(img, ocr, min_day_threshold=7, max_total_use=None):
    """
    从图片中按比例区域提取道具数量与剩余天数，判断是否需要继续使用道具。
    :param img: 截图图像
    :param ocr: PaddleOCR 实例
    :param min_day_threshold: 最少剩余天数阈值
    :param max_total_use: 最大可使用道具数（可选）
    :return: bool 是否继续使用
    """
    height, width = img.shape[:2]

    # 理智药数量 左上 左下 右上 右下 (1112.0, 460.0)  (1112.0, 500.0)  (1920.0, 460.0)  (1920.0, 500.0)
    # 理智药天数 左上 左下 右上 右下 (1086.0, 524.0)  (1086.0, 556.0)  (1920.0, 524.0)  (1920.0, 556.0)

    quantity_ocr = PaddleOCR(use_angle_cls=False, lang='en')
    # 计算区域位置
    quantity_region = img[
                      int(height * 0.41):int(height * 0.47),
                      int(width * 0.56):int(width * 0.95)
                      ]
    days_region = img[
                  int(height * 0.485):int(height * 0.515),
                  int(width * 0.566):int(width * 0.95)
                  ]

    # 定义阈值和最大值
    threshold_value = 250
    max_value = 255
    threshold_type = cv2.THRESH_BINARY
    _, quantity_region = cv2.threshold(quantity_region, threshold_value, max_value, threshold_type)

    # OCR 识别
    quantity_result = quantity_ocr.ocr(quantity_region, cls=False)
    days_result = ocr.ocr(days_region, cls=True)

    # 提取数字 + 位置信息（中心点x坐标用于匹配）
    def extract_numbers_with_x(result):
        data = []
        for word_info in result[0]:
            text = word_info[1][0]
            if re.fullmatch(r'\d{1,2}', text) or re.fullmatch(r'\d+天', text):
                x_center = sum([pt[0] for pt in word_info[0]]) / 4
                data.append((x_center, text))
        return data

    quantity_data = extract_numbers_with_x(quantity_result)
    days_data = extract_numbers_with_x(days_result)

    # 匹配：按x坐标排序，假设顺序一一对应
    quantity_data.sort()
    days_data.sort()
    item_list = []

    for (qx, qtext), (dx, dtext) in zip(quantity_data, days_data):
        try:
            count = int(qtext)
            days = int(re.sub(r'\D', '', dtext))  # 去除“天”
            item_list.append((count, days))
        except ValueError:
            continue  # OCR 错误不处理
    print(item_list)
    # 判断逻辑
    for count, days in item_list:  # 发现有临期的理智药
        if days <= min_day_threshold:  # 首先花掉 时间比设置的少 的理智药
            print(f"道具剩余 {days} 天，库存 {count}，继续使用")
            return True  # 继续运行

    if max_total_use:  # 若使用此参数
        total_available = sum([count for count, _ in item_list])  # 计算当前的理智药数量
        if total_available > max_total_use:  # 发现剩余理智药 很多
            print(f"总剩余道具 {total_available} > 阈值 {max_total_use}，继续使用")
            return True  # 继续运行

    # 没有临期的，也没有多余的
    print("没有即将过期的道具，或道具数量少，停止使用")
    return False  # 停止运行


if __name__ == '__main__':
    # map是滑动之后的图片

    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    print('123123123')
    print('123123123')
    print('123123123')
    print('123123123')
    print('123123123')
    print('123123123')
    print('123123123')

    """(1254, 666),第二个节点坐标，比例0.653125  (1383, 372)打完第二关的下一个节点坐标，比例0.7203125"""
    """(1257, 302),第二次测试，第二个节点坐标  (1288, 303)"""

    # connect.connect_mumu_emulator(16384)  # 连接到模拟器
    # img = connect.screen_shot()
    # #
    img = cv2.imread('rogue/aaa.png', 1)
    #
    # # 完成一个节点后查找后继坐标
    # _, cor = main_start.multi_ocr_process(ocr, img, '诡意行商')  # 寻找放弃按钮
    # cor1 = cor[0]
    # cor1 = (cor1[0]-95, cor1[1]-70)
    # print(cor)
    # print(cor1)
    # cv2.circle(img1, (1383, 372), 7, (0, 0, 255), -1)
    # cv_show(img1)

    # connect.connect_mumu_emulator(16384)  # 连接到模拟器
    # active.slide_press(1720, 540, 1000, 540, 2000)
    # os.system('cls')
    # img = connect.screen_shot(r'rogue/aaa.png')
    # active.click(1720, 150)
    #
    # a = BlackFlowActive.match_recruit_buttons(ocr)
    #
    scale_percent = 50  # 缩小到50%
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized_img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

    a = {'重装招募券': (526, 779), '术师招募券': (960, 779), '狙击招募券': (1394, 779)}
    # 绘制点与编号（坐标也需要按比例缩小）
    for point in a.values():
        # x = int(point[0] * scale_percent / 100)
        # y = int(point[1] * scale_percent / 100)
        x = point[0]
        y = point[1]
        cv2.circle(img, (x, y), 5, (0, 0, 255), -1)
    #
    # for i, (key, point) in enumerate(a.items(), 1):
    #     x = int(point[0] * scale_percent / 100)
    #     y = int(point[1] * scale_percent / 100)
    #     cv2.putText(resized_img, str(i), (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 显示图片
    cv2.imshow('Image with Points', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    #
    connect.end_connect()
    #
    # img1 = cv2.imread('rogue_blackflow/test/aaa.png', 1)
    # cv2.circle(img1, (1720, 150), 5, (0, 0, 255), -1)
    # cv2.imshow('Image with Points', img1)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # img = cv2.imread('rogue/zuozhan.png', 0)
    # counters = jiegarden_money.lunkuo(img)
    # nodes = jiegarden_money.level_ocr(img, ocr, 1080, level_name, event_name)
    # jiegarden_money.assign_unique_ids_to_nodes(nodes)  # 给每个节点加唯一ID
    # graph = jiegarden_money.build_graph_from_lines(counters, nodes)
    # paths = jiegarden_money.find_all_valid_paths(graph, level_name, 3)
    # print(paths)

    # flag, cor = main_start.ocr_process(ocr, img1, '行动力')
    # cor = find_center_coordinate(cor)
    # print(cor)
    # img1 = cv2.imread('image/screen.png', 1)
    # jiegarden_money.paint_circle(img1, cor)
    # #
    # ocr_result = ocr.ocr(img1, cls=True)  # 获取OCR识别结果
    # for i in ocr_result[0]:
    #     print(i)
    # print(flag, num)
    # cv_show(img)

    # img2 = cv2.imread('rogue/money_limit.png', 0)
    # # img2 = cv2.imread('image/num.png', 0)
    # img = cv2.imread('image/screen.png', 0)
    #
    # src_img = cv2.imread('image/screen.png', 1)
    # matchBool, row = img_Match(img2, img)
    # [{'x赶集': (238, 575)}, {'不期而遇': (898, 664)}, {'诡意行商': (1572, 574)}
    # cv2.circle(img1, (238, 575), 7, (0, 0, 255), -1)
    # cv_show(img1)


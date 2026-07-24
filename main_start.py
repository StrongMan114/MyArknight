"""
-*- coding: utf-8 -*-

@File: main_start.py
@author: 我的小熊掉了
@time: 2025/6/4 16:08
"""
import os
import sys

sys.path.append('./my_utils')
os.environ["ANDROID_SERIAL"] = "emulator-5554"

import re
import time
import cv2
from paddleocr import PaddleOCR
import difflib

from my_utils import active
from my_utils import connect
from my_utils.targetMatch import img_Match, find_center_coordinate

import logging

logging.disable(logging.DEBUG)  # 关闭DEBUG日志的打印
logging.disable(logging.WARNING)  # 关闭WARNING日志的打印


def is_fuzzy_match(name, level_names, cutoff=0.75):
    """是否模糊匹配到作战列表中的某一项"""
    match = difflib.get_close_matches(name, level_names, n=1, cutoff=cutoff)
    return len(match) > 0


# def ocr_process(creat_ocr, img, word_target: str):
#     """
#     :param creat_ocr: OCR模型
#     :param img: 要识别的图片
#     :param word_target: 目标文字
#     :return: 若识别到返回True和文字矩形框4个角的坐标，未识别到返回False和空列表
#     """
#     word = creat_ocr.ocr(img, cls=True)  # word[0] = [[坐标],[坐标]...]，("识别文字",识别准确率)]
#
#     coordinate = []
#     if word and word[0] is not None:
#         for i in word[0]:
#             print(i)
#         for line in word[0]:  # print(line[0], line[1][0], line[1][1])
#             if word_target == line[1][0]:  # line[1][0] 为"识别文字"
#                 return True, line[0]
#             elif is_fuzzy_match(word_target, [line[1][0]]):
#                 return True, line[0]
#     return False, coordinate


def ocr_process(creat_ocr, img, word_target: str):
    """
    :param creat_ocr: OCR模型
    :param img: 要识别的图片
    :param word_target: 目标文字
    :return: 若识别到返回True和文字矩形框4个角的坐标，未识别到返回False和空列表
    """
    word = creat_ocr.ocr(img, cls=True)

    coordinate = []
    if word and word[0] is not None:
        # 三级匹配cutoff值，从高到低
        cutoff_levels = [0.93, 0.84, 0.78]
        # 三级模糊匹配，每级遍历所有数据
        for cutoff in cutoff_levels:
            for line in word[0]:
                recognized_text = line[1][0]
                if is_fuzzy_match(word_target, [recognized_text], cutoff):
                    print(f'模糊匹配成功: {recognized_text} -> {word_target}, cutoff={cutoff}')
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


def extract_question_and_number(ocr_result, pattern):
    """
    文字识别检测理智药使用情况
    return: tuple: (是否找到问题, 提取的数字) 如 (True, 160) 或 (False, None)
    """
    # 遍历所有识别到的文本行
    if ocr_result and ocr_result[0] is not None:
        for line in ocr_result:
            for word_info in line:
                text = word_info[1][0]  # 提取识别文本
                match = re.search(pattern, text)
                if match:
                    # 提取数字并转换为整数
                    number = int(match.group(1))  # match.group(0)是匹配的整体，match.group(1)为第一个括号里匹配的东西
                    return True, number
    # 如果没有找到匹配的问题
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
        for line in result:
            for word_info in line:
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

    # 判断逻辑
    if min_day_threshold:
        for count, days in item_list:  # 发现有临期的理智药
            if days <= min_day_threshold:  # 首先花掉 时间比设置的少 的理智药
                print(f"道具剩余 {days} 天，库存 {count}，继续使用")
                return True  # 继续运行

    if max_total_use:
        total_available = sum([count for count, _ in item_list])  # 计算当前的理智药数量
        print(f'总剩余道具{total_available}')
        if total_available > max_total_use:  # 发现剩余理智药 很多
            print(f"总剩余道具 {total_available} > 阈值 {max_total_use}，继续使用")
            return True  # 继续运行

    # 没有临期的，也没有多余的
    print("没有即将过期的道具，或道具数量少，停止使用")
    return False  # 停止运行


if __name__ == '__main__':
    """
      打开要打的关卡，右下角有代理指挥和开始作战的界面，然后启动程序，设置好min_day_threshold与max_total_use
    """
    # level = '1 - 7'
    level = 'AD-7'
    # 优先使用临期道具，若道具剩余时间小于min_day_threshold则全部用掉,测试时min_day_threshold = 0；max_total_use = 100
    min_day_threshold = 3  # 理智药天数，剩余时间大于这个数值的理智药不会使用 min_day_threshold以下都为临期道具
    max_total_use = 22  # 最后剩余的理智药数量 剩余的在max_total_use以上才会继续运行

    operate_flag = True
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')  # 加载文字识别ocr模块

    is_connect = connect.connect_mumu_emulator(16384)  # 连接到模拟器
    print('连接状态:', is_connect)
    # # 启动游戏
    # if not is_application_operation(arknights_bilibili):  # 参数为应用程序包名称
    #     connect.start_arknights_bilibili()  # 打开bilibili服明日方舟
    """这里循环"""
    while operate_flag:
        start_time = time.time()
        print('选择关卡后，设置代理指挥，只能手动设置倍数')
        img = connect.screen_shot('image/aaa.png', 0)
        img1 = cv2.imread('image/num.png', 0)
        o1, cor1 = ocr_process(ocr, img, '代理指挥')
        o2, cor2 = ocr_process(ocr, img, '代理指挥+')
        click_coor = [0, 0]
        if o1:
            matchBool, (row1, col1) = img_Match(img1, img)
            if not matchBool:
                print('代理指挥未勾选，准备点击代理指挥')
                # 点击代理指挥
                click_coor = find_center_coordinate(cor1)
                active.click(click_coor[0], click_coor[1])
        elif o2:
            print('代理指挥已经点击')
        else:
            print('没有识别到代理指挥')
        del o1, o2, cor1, cor2, click_coor, img, img1

        print('开始行动')
        time.sleep(2)
        cor = [0, 0]
        img1 = cv2.imread('image/start.png', 0)
        start_flag = False
        while not start_flag:
            print('等待任务开始界面')
            img = connect.screen_shot('image/aaa.png', 0)
            o1, cor = ocr_process(ocr, img, '开始行动')
            start_flag = o1
        click_coor = find_center_coordinate(cor)
        active.click(click_coor[0], click_coor[1])
        del o1, cor, img1, start_flag, img, click_coor

        """查看理智是否不够消耗"""
        # 是否花费以上理智合剂提升160理智？
        print('理智药')
        time.sleep(2)
        img = connect.screen_shot('image/aaa.png', 0)  # 截图
        pattern1 = r'是否花费\d*至纯源石兑换(\d+)'
        pattern2 = r'是否花费以上理智合剂提升(\d+)'
        img0 = cv2.imread('image/yuanshi.png', 0)
        img1 = cv2.imread('image/lizhi_no.png', 0)
        img2 = cv2.imread('image/lizhi_yes.png', 0)
        ocr_result = ocr.ocr(img, cls=True)  # 获取OCR识别结果
        yuanshi_n, _ = img_Match(img0, img)  # 检测是否为消耗源石界面
        flag, _ = extract_question_and_number(ocr_result, pattern1)  # 检测是否为消耗源石界面
        n = False
        cor = []

        if flag or yuanshi_n:  # 双重判断，若为消耗源石界面
            operate_flag = False  # 设置运行位为 停止
            _, cor = img_Match(img1, img)  # 检测 X 号
            active.click(cor[0], cor[1])  # 关闭源石换理智界面
            time.sleep(5)
            # gracefully_close_arknights()  # 优雅地关闭游戏
            connect.end_connect()  # 结束连接
            sys.exit('理智药消耗光了，不能花石头')

        flag, num = extract_question_and_number(ocr_result, pattern2)  # 检测是否为消耗理智药界面
        flag_ocr, _ = ocr_process(ocr, img, '清空选择')
        if flag or flag_ocr:  # 若为消耗理智药界面
            # 若剩余天数确实很多，道具数量过少
            if not extract_items_by_region(img, ocr, min_day_threshold=min_day_threshold,
                                           max_total_use=max_total_use):  # 检测理智药剩余数量
                operate_flag = False  # 设置运行位为 停止
                _, cor = img_Match(img1, img)
                active.click(cor[0], cor[1])  # 关闭理智药界面
                time.sleep(5)
                # gracefully_close_arknights()
                connect.end_connect()
                sys.exit("脚本终止：无即将过期道具，或库存不足")

            n, cor = img_Match(img2, img)  # 若理智药符合运行数量  匹配使用的对号图案
            if n:  # 匹配 对号 成功后
                active.click(cor[0], cor[1])  # 使用理智药
                print('使用理智药开始行动')  # 继续开始行动
                time.sleep(3)  # 等待使用后的界面

                # 使用理智药后可能退出开始界面
                img = connect.screen_shot('image/aaa.png', 0)
                o2, cor2 = ocr_process(ocr, img, '开始行动')
                if not o2:
                    img = connect.screen_shot('image/aaa.png', 0)
                    o1, cor1 = ocr_process(ocr, img, level)
                    if o1:
                        print('点击关卡')
                        click_coor = find_center_coordinate(cor1)
                        active.click(click_coor[0], click_coor[1])  # 选中关卡
                        del cor1, click_coor, o1
                    else:
                        print(f'没有识别到关卡{level}')

                time.sleep(3)  # 等待使用后的界面
                cor2 = find_center_coordinate(cor2)
                print('点击开始行动')
                active.click(cor2[0], cor2[1])  # 点击开始行动—>编队界面

                del o2, cor2
        del img, img1, img2, ocr_result, flag, n, cor, flag_ocr, yuanshi_n

        print('编队界面')
        time.sleep(4)
        img = connect.screen_shot('image/aaa.png', 0)
        img1 = cv2.imread('image/biandui.png', 0)
        click_coor = [0, 0]
        flag, _ = img_Match(img1, img)  # 找到为真，没找到为假
        while not flag:  # flag为假 没找到 while循环继续找
            print('寻找是否为编队界面')
            flag, _ = img_Match(img1, img)
            time.sleep(0.5)

        o1, cor = ocr_process(ocr, img, '开始')
        if o1:
            click_coor = find_center_coordinate(cor)
            active.click(click_coor[0], click_coor[1])
        else:
            print('编队界面没找到 开始行动')
        del flag, o1, cor, img, img1

        print('等待任务结束')
        time.sleep(15)
        img1 = cv2.imread('image/end.png', 0)
        img = connect.screen_shot('image/aaa.png', 0)
        flag, cor = img_Match(img1, img)  # 找到为真，没找到为假

        while not flag:  # flag为假 while循环
            time.sleep(15)
            print('等待任务结束')
            img = connect.screen_shot('image/aaa.png', 0)
            flag, cor = img_Match(img1, img)

        time.sleep(3)
        active.click(cor[0], cor[1])  # 退出任务结束界面
        del img, img1, flag, cor,

        time.sleep(3)  # 等待任务退出
        flag = False
        while flag:
            print('等待退出')
            img = connect.screen_shot('image/aaa.png', 0)
            flag, _ = ocr_process(ocr, img, '开始行动')
            time.sleep(1)  # 等待任务退出

        end_time = time.time()
        print(f'一次关卡花费{end_time - start_time}秒')

"""
-*- coding: utf-8 -*-

@File: jiegarden_money.py
@author: 我的小熊掉了
@time: 2025/7/16 15:08
"""
import os
import time
import gc
import main_start
from memory_profiler import profile
import jieGarden_active
import logging

logging.disable(logging.DEBUG)  # 关闭DEBUG日志的打印
logging.disable(logging.WARNING)  # 关闭WARNING日志的打印
os.environ['FLAGS_allocator_strategy'] = 'naive_best_fit'

import sys
sys.path.append('./my_utils')

import cv2
import numpy as np
from paddleocr import PaddleOCR
import difflib
from collections import deque
from my_utils import targetMatch
from my_utils import active
from my_utils import connect


def lunkuo(img):  # 白线轮廓 返回轮廓最左边和最右边的值
    # 转灰度
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 二值化提取白线特征（白色接近255）
    _, binary = cv2.threshold(img, 230, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3, 3), np.uint8)
    dst = cv2.erode(binary, kernel, iterations=2)
    # 线段检测
    contours, _ = cv2.findContours(dst, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # print(len(contours[1]))

    # cv2.drawContours(img, contours, -1, (0, 0, 255), 1)
    # targetMatch.cv_show(img)
    return contours


def find_left_right_points(data):  # 返回最左边和最右边的点
    # 将数据转换为二维数组形式
    a = []
    points = data.reshape(-1, 2)
    # 找到x坐标最小的点（最左边）
    leftmost = points[np.argmin(points[:, 0])]
    # 找到x坐标最大的点（最右边）
    rightmost = points[np.argmax(points[:, 0])]
    # print(leftmost, rightmost)
    a.extend(leftmost)
    a.extend(rightmost)
    return a


def build_graph_from_lines(contours, nodes):
    """
    根据轮廓和节点，构建有向图结构，解决同名节点合并问题
    :param contours: 线段列表（每段为一组点）
    :param nodes: 所有节点（需包含 id）
    :return: graph = { node_id: {name, click_center, edges: [ {id, name, click_center}, ... ] } }
    """
    graph = {}
    ls = []

    for contour in contours:
        if len(contour) >= 2:
            ls.append(find_left_right_points(contour))

    for line in ls:
        x1, y1, x2, y2 = line

        start_node = find_node_by_point((x1, y1), nodes)
        end_node = find_node_by_point((x2, y2), nodes)

        if start_node and end_node and start_node["id"] != end_node["id"]:
            graph.setdefault(start_node["id"], {
                "name": start_node["name"],
                "click_center": start_node["click_center"],
                "edges": []
            })
            graph[start_node["id"]]["edges"].append({
                "id": end_node["id"],
                "name": end_node["name"],
                "click_center": end_node["click_center"]
            })

    return graph


def is_fuzzy_match(name, level_names, cutoff=0.3):
    """是否模糊匹配到作战列表中的某一项"""
    match = difflib.get_close_matches(name, level_names, n=1, cutoff=cutoff)
    return len(match) > 0


def find_all_valid_paths(graph, level, max_depth=5):
    """
    搜索所有包含 战斗+不期而遇/得偿所愿+不期而遇/得偿所愿 的路径，每条路径最多包含 max_depth 个节点
    :param graph: 有向图
    :return: list of path dicts: [[{name: (x, y)}, ...], ...]
    """
    valid_paths = []

    for start_id in graph:
        queue = deque()
        queue.append(([(graph[start_id]["name"], graph[start_id]["click_center"])], start_id, {start_id}))

        while queue:
            path_with_coords, current_id, visited = queue.popleft()

            names_in_path = [name for name, _ in path_with_coords]
            has_fight = any(is_fuzzy_match(name, level, 0.6) for name in names_in_path)
            has_encounter = any("不期而遇" in name for name in names_in_path)
            has_trader = any("诡意行商" in name for name in names_in_path)

            if has_fight and has_encounter and has_trader and len(path_with_coords) == 3:
                path_as_dict = [{name: coord} for name, coord in path_with_coords]
                valid_paths.append(path_as_dict)
                continue

            if len(path_with_coords) >= max_depth:
                continue

            for neighbor in graph.get(current_id, {}).get("edges", []):
                neighbor_id = neighbor["id"]
                if neighbor_id not in visited:
                    new_path = path_with_coords + [(neighbor["name"], neighbor["click_center"])]
                    queue.append((new_path, neighbor_id, visited | {neighbor_id}))

    return valid_paths


def find_node_by_point(point, nodes):
    """
    根据线段端点，找到包含该点的节点
    :param point: (x, y)
    :param nodes: 所有节点
    :return: 节点字典（包含 id, name, click_center, box），或 None
    """
    for node in nodes:
        x1, y1, x2, y2 = node["box"]
        if x1 <= point[0] <= x2 and y1 <= point[1] <= y2:
            return node
    return None


def level_ocr(img, ocr, img_height, level, event_level):
    # img灰度图

    # OCR 识别
    results = ocr.ocr(img, cls=True)
    nodes = []
    for line in results[0]:
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = line[0]
        text = line[1][0].strip()
        # score = line[1][1]

        text_flag = False
        if is_fuzzy_match(text, level, 0.4) or is_fuzzy_match(text, event_level, 0.4):
            text_flag = True

        if (y1 > img_height * 0.3 and y2 < img_height * 0.8) and text_flag:
            # 可以加入过滤条件，如中文长度、置信度
            # if (score > 0.8) or text_flag:
            x_min = int(min(x1, x2, x3, x4))
            y_min = int(min(y1, y2, y3, y4))
            x_max = int(max(x1, x2, x3, x4))
            y_max = int(max(y1, y2, y3, y4))
            click_center = (((x_min + x_max) // 2) - 95, ((y_min + y_max) // 2) - 70)  # 关卡中间

            nodes.append({
                "name": text.lower().replace(" ", ""),
                "box": (((x_min + x_max) // 2) - 245, ((y_min + y_max) // 2) - 120, x_max + 40, y_max - 10),
                "click_center": click_center
            })
    return nodes


def assign_unique_ids_to_nodes(nodes):
    for node in nodes:
        x, y = node["click_center"]
        node["id"] = f"{node['name']}_{x}_{y}"


def paint_circle(src_img, coordinate):
    cv2.circle(src_img, (coordinate[0], coordinate[1]), 7, (0, 0, 255), -1)
    targetMatch.cv_show(src_img)


def load_all_templates():
    """统一加载模板图像，避免重复读取"""
    return {
        "team_enter": cv2.imread('rogue/team_enter.png', 0),
        "team_quit": cv2.imread('rogue/quit_enter.png', 0),
        "tongbao_enter": cv2.imread('rogue/tongbao_enter.png', 0),
        "battle_setting": cv2.imread('rogue/setting.png', 0),
        "battle_quit": cv2.imread('rogue/quit_battle.png', 0),
        "event_exit": cv2.imread('rogue/event_exit.png', 0),
        "event_money": cv2.imread('rogue/event_money.png', 0),
        "event_exit_enter": cv2.imread('rogue/event_exit_enter.png', 0),
        "exit": cv2.imread('rogue/exit.png', 0),
        "epoch_end_enter": cv2.imread('rogue/end_enter.png', 0)
    }


@profile(precision=4, stream=open('memory_profiler.log', 'a+', encoding='utf-8'))
def main_loop(ocr, templates, height, width, max_rounds=100):
    """
    :param ocr: ocr模型
    :param templates: load_all_templates()加载的图片
    :param height: 模拟器分辨率 高
    :param width: 模拟器分辨率 宽
    :param max_rounds: 最大循环次数
    :return: None
    """
    level_name = ['x老戏骨', 'x狡鼷三窟', 'x赶集', 'x正经生意', 'x紧急作战', 'x作战']
    event_name = ['不期而遇', '诡意行商']

    second_node_width = 0.653125 * width

    for cnt in range(max_rounds):
        try:
            # --- 进入本局 ---
            cor = jieGarden_active.start(ocr)
            jieGarden_active.select_team(templates["team_enter"], cor)
            jieGarden_active.select_ticket(templates["team_enter"], ocr)
            jieGarden_active.select_character(templates["team_quit"], templates["tongbao_enter"], ocr)

            # --- 识别路径 ---
            active.slide(width * 0.8, height * 0.5, width * 0.72, height * 0.5)
            time.sleep(2)
            img = connect.screen_shot('rogue/zuozhan.png')

            contours = lunkuo(img)
            nodes = level_ocr(img, ocr, height, level_name, event_name)
            assign_unique_ids_to_nodes(nodes)
            graph = build_graph_from_lines(contours, nodes)
            paths = find_all_valid_paths(graph, level_name, 3)
            print(paths)
            del contours, nodes, img  # 主动清理临时变量
            gc.collect()

            # --- 执行路径 ---
            forward_flag = False
            if paths:
                forward_flag = True
                for i, node in enumerate(paths[0]):
                    category, _, cor = jieGarden_active.select_path(paths, level_name, i)
                    if i == 0:
                        active.click(cor[0], cor[1])
                    else:
                        active.click(second_node_width, cor[1])
                    time.sleep(1.7)

                    if category == 1:
                        jieGarden_active.battle_process(ocr, templates["team_quit"], templates["battle_setting"],
                                                        templates["battle_quit"])
                    elif category == 2:
                        jieGarden_active.event_process(ocr, templates["event_exit"], templates["event_money"],
                                                       templates["event_exit_enter"])
                    elif category == 3:
                        jieGarden_active.store_process(ocr)
            else:
                print('未识别到有效路径')

            # --- 退出本局 ---
            jieGarden_active.end_process(forward_flag, ocr, templates["exit"], templates["team_quit"],
                                         templates["epoch_end_enter"],
                                         is_activity_experience=True,
                                         is_mouth_task=True,
                                         is_character_experience=True)

        except Exception as e:
            print(f'[异常] 第 {cnt} 轮运行出错: {e}')

        # del img, contours, nodes, graph, paths
        # gc.collect()
        time.sleep(1.0)  # 控制速度


if __name__ == '__main__':
    ocr1 = PaddleOCR(use_angle_cls=True, lang='ch')
    templates1 = load_all_templates()

    connect.connect_mumu_emulator(16384)
    img1 = connect.screen_shot()
    height, width = img1.shape[:2]

    epoch = 30
    for i in range(epoch):
        print(f'\n第 {i + 1} 轮 | 当前时间: {time.strftime("%H:%M:%S")}')
        main_loop(ocr1, templates1, height, width, max_rounds=1)
    connect.end_connect()

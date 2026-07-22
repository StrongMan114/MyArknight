"""
-*- coding: utf-8 -*-

@File: rogue_test.py
@author: 我的小熊掉了
@time: 2025/7/16 15:09
"""
import logging

logging.disable(logging.DEBUG)  # 关闭DEBUG日志的打印
logging.disable(logging.WARNING)  # 关闭WARNING日志的打印

import sys

sys.path.append('./my_utils')

import cv2
import numpy as np
import difflib
from collections import deque
from paddleocr import PaddleOCR

import jiegarden_money

from my_utils import targetMatch


def lunkuo(img):  # 白线轮廓 返回轮廓最左边和最右边的值
    # 输出彩色图像
    # 转灰度
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 二值化提取白线特征（白色接近255）
    _, binary = cv2.threshold(img, 230, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3, 3), np.uint8)
    dst = cv2.erode(binary, kernel, iterations=1)

    # targetMatch.cv_show(dst)
    # 线段检测
    contours, _ = cv2.findContours(dst, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # cv2.drawContours(img, contours, -1, (0, 0, 255), 1)
    # targetMatch.cv_show(img)
    return contours


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


def rectangle():
    for i in nodes:
        if i['name'] == '不期而遇':
            cor1 = i['center']  # 文字中间
            cor2 = i['click_center']

            x_add = 150
            y_add = 50

            top_left_corner = (cor2[0] - x_add, cor2[1] - y_add)
            bottom_right_corner = (cor2[0] + x_add, cor2[1] + y_add)

            # 在图片上绘制矩形框
            color = (0, 255, 0)  # BGR格式，绿色
            thickness = 2  # 线条的厚度
            cv2.rectangle(img1, top_left_corner, bottom_right_corner, color, thickness)

            # cv2.circle(img1, (cor1[0], cor1[1]), 10, (0, 0, 255), -1)
            # cv2.circle(img1, (cor2[0], cor2[1]), 10, (255, 0, 0), -1)

            targetMatch.cv_show(img1)


def level_ocr(img, ocr):
    # img灰度图
    height, width = img.shape[:2]

    # OCR 识别
    results = ocr.ocr(img, cls=True)
    nodes = []
    for line in results[0]:
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = line[0]
        text = line[1][0].strip()
        score = line[1][1]
        print(text, score)

        if y1 > height * 0.3 and y2 < height * 0.8:
            # 可以加入过滤条件，如中文长度、置信度
            if score > 0.75:
                x_min = int(min(x1, x2, x3, x4))
                y_min = int(min(y1, y2, y3, y4))
                x_max = int(max(x1, x2, x3, x4))
                y_max = int(max(y1, y2, y3, y4))
                center = (((x_min + x_max) // 2), ((y_min + y_max) // 2))
                click_center = (((x_min + x_max) // 2) - 95, ((y_min + y_max) // 2) - 70)  # 关卡中间

                nodes.append({
                    "name": text.lower().replace(" ", ""),
                    "box": (((x_min + x_max) // 2) - 245, ((y_min + y_max) // 2) - 120, x_max + 20, y_max),
                    "click_center": click_center
                })
    return nodes


def is_fuzzy_match(name, level_names, cutoff=0.2):
    """是否模糊匹配到作战列表中的某一项"""
    match = difflib.get_close_matches(name, level_names, n=1, cutoff=cutoff)
    return len(match) > 0


def find_all_valid_paths(graph, max_depth=5):
    """
    搜索所有包含 战斗+不期而遇+诡意行商 的路径，每条路径最多包含 max_depth 个节点
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
            has_fight = any("x" in name or "战" in name for name in names_in_path)
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


def assign_unique_ids_to_nodes(nodes):
    for node in nodes:
        x, y = node["click_center"]
        node["id"] = f"{node['name']}_{x}_{y}"


if __name__ == '__main__':
    level_name = ['x老戏骨', 'x狡鼷三窟', 'x赶集', 'x正经生意', '不期而遇', '诡意行商', '得偿所愿', 'x紧急作战']
    envent = {'传讯': '离开'}

    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    image_path = 'rogue/zuozhan.png'
    img = cv2.imread(image_path, 0)

    counters = lunkuo(img)
    # print(len(counters))
    nodes = jiegarden_money.level_ocr(img, ocr, 1080, level_name)
    # print(nodes)
    assign_unique_ids_to_nodes(nodes)  # 给每个节点加唯一ID
    graph = build_graph_from_lines(counters, nodes)  # 构建图
    paths = find_all_valid_paths(graph)  # 搜索满足条件的路径

    # 输出
    for path in paths:
        print(path)
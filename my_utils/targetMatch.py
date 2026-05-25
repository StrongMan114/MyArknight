"""
-*- coding: utf-8 -*-

@File: targetMatch.py
@author: 我的小熊掉了
@time: 2025/1/13 10:24
"""
import math
from typing import List, Tuple
import cv2
import subprocess
import connect


def cv_show(img, name: str = 'imgShow'):
    """

    :param img: 窗口名称
    :param name: 需要显示的图像
    :return: None
    """
    cv2.namedWindow("window", cv2.WINDOW_NORMAL)  # 允许调整窗口
    cv2.imshow("window", img)
    cv2.waitKey(0)


def find_center_coordinate(coordinateList):
    """

    :param coordinateList: 存储坐标的列表 (row,col)
    :return: 返回所有坐标的中心值
    """
    try:
        max1 = max2 = 0
        min1 = min2 = math.inf
        for row, col in coordinateList:
            max1 = max(row, max1)
            min1 = min(row, min1)

            max2 = max(col, max2)
            min2 = min(col, min2)

        # print(max1, max2, min1, min2)
        # print((max1, min2), (max1, max2), (min1, min2), (min1, max2))
        center_y = int((max1 + min1) / 2)
        center_x = int((max2 + min2) / 2)
    except:
        center_y = 0
        center_x = 0
    return center_y, center_x


def img_Match(imgSmall, imgBig):
    """

    :param imgBig: # 大图
    :param imgSmall: # 大图中的部分图像
    :return: 若找到则返回True与目标坐标,未找到返回False与0，0
    """
    # src_img = cv2.imread('image/3.png', 1)
    match_num = 20
    threshold = 70
    try:
        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(imgSmall, None)
        kp2, des2 = sift.detectAndCompute(imgBig, None)
        # crossCheck表示两个特征点要互相匹配，例如A中的第i个特征点与B中的第j个特征点最近的，并且B中的第j个特征点到A中的第i个特征点也是
        # NORM_L2: 归一化数组的(欧几里德距离)，如果其他特征计算方法需要考虑不同的匹配计算方式
        bf = cv2.BFMatcher(crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)

        coordinateList = []

        for m_data in matches[:match_num]:
            if m_data.distance < threshold:
                # 以下 为一个 cv2.KeyPoint 对象， pt返回坐标
                # (int(cnt[0]), int(cnt[1])) 就是得到的对应点的坐标
                cnt = kp2[m_data.trainIdx].pt  # 大图中的KeyPoint
                # cv2.circle(src_img, (int(cnt[0]), int(cnt[1])), 5, (0, 0, 255), -1)
                coordinateList.append((int(cnt[0]), int(cnt[1])))
        # cv_show("result", src_img)
        # print(coordinateList)
        if len(coordinateList) == 0:
            return False, (0, 0)
        else:
            row, col = find_center_coordinate(coordinateList)
            return True, (row, col)

    except Exception as e:
        print('error catch')
        print(f"没有任何匹配点")
        return False, (0, 0)


if __name__ == '__main__':
    img1 = cv2.imread('image/yuanshi.png', 0)  # 大图中的部分图像
    img2 = connect.screen_shot('image/aaa.png')
    src_img = cv2.imread('image/aaa.png', 1)
    matchBool, (row1, col1) = img_Match(img1, img2)
    if matchBool:
        cv2.circle(src_img, (row1, col1), 5, (0, 0, 255), -1)
        print(row1, col1)
        cv_show(src_img)
    else:
        print('没找到图片')

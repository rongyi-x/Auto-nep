#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：find_train.py
@Author ：RongYi
@Date ：2025/5/15 15:32
@E-mail ：2071914258@qq.com
"""
from ase.io import read, write
import numpy as np


def find_struc(train_xyz, dataset, precision=0):
    """
    从数据集里面找 train.xyz
    :param train_xyz:
    :param dataset:
    :return:
    """
    shifted_xyz = read(train_xyz, format='extxyz', index=':')
    no_shifted_xyz = read(dataset, format='extxyz', index=':')

    len1 = len(shifted_xyz)
    len2 = len(no_shifted_xyz)
    print("shifted_xyz length:", len1)
    print("no_shifted_xyz length:", len2)

    # no_shifted_xyz -> shifted_xyz:
    # shifted_index (0, 439)

    # if no_shifted_xyz[no_shifted_index] = shifted_xyz[shifted_index] : ok
    # else no_shifted_index += 1

    # # test
    # test1 = np.around(shifted_xyz[1].get_positions(), 3)
    # test2 = np.around(no_shifted_xyz[2].get_positions(), 3)
    # print((test1 == test2).all())

    total_index = []
    no_in1 = []
    no_in2 = []
    for shifted_index in range(len1):
        # 初始化 pos1 pos2 no_shifted_index
        no_shifted_index = 0
        pos1 = np.around(shifted_xyz[shifted_index].get_positions(), precision)
        pos2 = np.around(no_shifted_xyz[no_shifted_index].get_positions(), precision)

        while True:
            if len(pos1) != len(pos2):
                if no_shifted_index < len(no_shifted_xyz) - 1:
                    no_shifted_index += 1
                    pos2 = np.around(no_shifted_xyz[no_shifted_index].get_positions(), precision)
                else:
                    no_in2.append(shifted_index)
                    print("skip")
                    break
            else:
                # 位置一样 跳出循环
                if ((pos1 == pos2).all()):
                    with open("./index.txt", "a") as f:
                        f.write(f"shifted_index: {shifted_index} -> no_shifted_index: {no_shifted_index}\n")
                    total_index.append(no_shifted_index)
                    break
                else:
                    same_elements = np.sum(pos1 == pos2)
                    total_elements = pos1.size
                    similarity_ratio = same_elements / total_elements
                    if similarity_ratio >= 0.99:
                        print(f"{shifted_index} ~ {no_shifted_index} {similarity_ratio}% 的元素相同")
                        total_index.append(no_shifted_index)
                        break
                    if no_shifted_index < len(no_shifted_xyz) - 1:
                        no_shifted_index += 1
                        pos2 = np.around(no_shifted_xyz[no_shifted_index].get_positions(), precision)
                    else:
                        no_in2.append(shifted_index)
                        print("skip")
                        break
    for i in range(len2):
        if i not in total_index:
            no_in1.append(i)
    select_no_shifted_xyz = [no_shifted_xyz[index] for index in total_index]
    no_in1_xyz = [no_shifted_xyz[index] for index in no_in1]
    no_in2_xyz = [shifted_xyz[index] for index in no_in2]
    write('./find_no_shifted.xyz', select_no_shifted_xyz, format='extxyz')
    write('./no_in1.xyz', no_in1_xyz, format='extxyz')
    write('./no_in2.xyz', no_in2_xyz, format='extxyz')
    print("OK!Write find_no_shifted.xyz")


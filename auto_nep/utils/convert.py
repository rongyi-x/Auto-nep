#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：convert.py
@Author ：RongYi
@Date ：2025/6/8 10:14
@E-mail ：2071914258@qq.com
"""

from ase.io import read, write
from tqdm import tqdm
import os
import re


def find_pp_basis(elements_list, pp_path, basis_path):
    """
    寻找基组赝势文件
    :param config:
    :return:
    """
    pp, basis = {}, {}

    for index, element_type in enumerate(elements_list):
        pp_flag, basis_flag = False, False  # 标志位
        # pp_pattern: 以元素类型开头, 以.upf结尾
        pp_pattern = rf'^{element_type}[._].*upf$'
        # basis_pattern: 以元素类型开头, 以.orb结尾
        basis_pattern = rf'^{element_type}[._].*orb$'

        for filename in os.listdir(pp_path):
            if re.match(pp_pattern, filename):
                pp[f'{element_type}'] = filename
                pp_flag = True
                break

        for filename in os.listdir(basis_path):
            if re.match(basis_pattern, filename):
                basis[f'{element_type}'] = filename
                basis_flag = True
                break

        if pp_flag is False:
            print(f'未找到 {element_type} 赝势文件, 请检查 {pp_path}')
            exit()
        if basis_flag is False:
            print(f'未找到 {element_type} 轨道文件, 请检查 {basis_path}')
            exit()
    print(f'赝势文件: {pp}')
    print(f'轨道文件: {basis}')
    return pp, basis


def convert_format(xyz):
    """
    转换 xyz 文件变成 abacus 的 STRU 文件
    :param xyz: xyz 文件路径
    :return:
    """
    # 获取用户文件夹路径
    user_folder = os.path.expanduser("~")

    # 创建.env 文件的路径
    env_file_path = os.path.join(user_folder, ".auto_nep_env")

    # 检查文件是否存在
    if not os.path.exists(env_file_path):
        print(f"文件 {env_file_path} 不存在")
        exit()

    # 读取.env 文件
    env_vars = {}
    with open(env_file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key] = value

    # 获取 pp_path 和 basis_path 的值
    pp_path_value = env_vars.get("pp_path")
    basis_path_value = env_vars.get("basis_path")

    print(f"pp_path: {pp_path_value}")
    print(f"basis_path: {basis_path_value}")

    all_frames = read(xyz, index=":")
    print(len(all_frames))
    # 展平 获取元素
    flatten_comprehension = lambda matrix: [item for row in matrix for item in row]
    elements_list = sorted(set(flatten_comprehension([i.get_chemical_symbols() for i in all_frames])))
    pp, basis = find_pp_basis(elements_list, pp_path_value, basis_path_value)

    for i in tqdm(range(1, len(all_frames) + 1)):
        os.makedirs(f"./xyz2abacus/{i}", exist_ok=True)
        write(f"./xyz2abacus/{i}/STRU", all_frames[i-1], format='abacus', pp=pp, basis=basis)
    print("格式转换完成!")

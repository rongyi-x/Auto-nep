#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：shift_energy.py
@Author ：RongYi
@Date ：2025/5/2 13:01
@E-mail ：2071914258@qq.com
"""
import numpy as np
from ase.io import read, write

def SVD_A(A, b):
    """
    奇异矩阵分解 solve A * x=b
    :param A: Coefficient matrix of shape (m, n)
    :param b: Right-hand side vector of shape (m, )
    :return: Solution vector of shape (n, )
    """
    U, S, V = np.linalg.svd(A)
    B = U.T @ b
    X = B[:len(S), :]/S.reshape(len(S), -1)
    x = V.T @ X  # attention
    return x


def shift_energy(xyz, filename="shifted.xyz"):
    """
    能量平移
    :param xyz: xyz 文件
    :return: None
    """
    # 读取所有帧
    all_frames = read(xyz, index=":")

    # 提取所有唯一的元素
    flatten_comprehension = lambda matrix: [item for row in matrix for item in row]
    all_elements = sorted(set(flatten_comprehension([i.get_chemical_symbols() for i in all_frames])))

    # 初始化组成矩阵和能量矩阵
    composition_matrix = np.zeros((len(all_frames), len(all_elements)))
    energy_matrix = np.zeros((len(all_frames), 1))

    # 获取每一帧内 各个元素出现的次数 composition_matrix 以及结构能量
    for i in range(len(all_frames)):
        for j in range(len(all_elements)):
            composition_matrix[i][j] = all_frames[i].get_chemical_symbols().count(all_elements[j])
        try:
            energy_matrix[i][0] = all_frames[i].get_potential_energy()
        except RuntimeError:
            energy_matrix[i][0] = all_frames[i].info["Energy"]

    # 如果矩阵的秩小于列数 欠定 需要添加约束使矩阵可解
    if np.linalg.matrix_rank(composition_matrix) < len(all_elements):
        print("Warning! The composition_matrix is underdetermined, adding constrains....")
        number_of_constrains = len(all_elements) - np.linalg.matrix_rank(composition_matrix)
        import itertools
        to_add_constrain_pairs = []
        for i in itertools.combinations(range(len(all_elements)), 2):
            additional_matrix = np.zeros(len(all_elements))
            additional_matrix[i[0]] = 1
            additional_matrix[i[1]] = -1
            additional_energy = np.zeros(1)
            composition_matrix = np.r_[composition_matrix, [additional_matrix]]
            energy_matrix = np.r_[energy_matrix, [additional_energy]]

    # 计算每个原子的基态能量
    atomic_shifted_energy = SVD_A(composition_matrix, energy_matrix)
    for i in range(len(all_elements)):
        print("%s:%f" % (all_elements[i], atomic_shifted_energy[i][0]), end=' ')

    # 平移后能量 = 平移前能量 - composition_matrix(m, 3) @ atomic_shifted_energy(3, 1)
    shifted_energy = (energy_matrix - np.matmul(composition_matrix, atomic_shifted_energy)).flatten()

    print(f"\nAveraged energies now: {shifted_energy.mean():.10f} eV.")
    print(f"Absolute maximum energy now: {max(abs(shifted_energy)):.10f} eV.")

    # 输出所有帧
    for i in range(len(all_frames)):
        try:
            forces = all_frames[i].get_forces()
            all_frames[i].new_array('forces', forces)
        except:
            pass
        all_frames[i].calc = None
        all_frames[i].info['energy'] = shifted_energy[i]
    write(filename, all_frames)


#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：perturb.py
@Author ：RongYi
@Date ：2025/5/9 17:40
@E-mail ：2071914258@qq.com
"""
import numpy as np
from ase.io import read, write
from tqdm import tqdm
from auto_nep.sysprint import sysprint


class Perturb:
    def __init__(self, num, min_distance, cell_perturb_coefficient):
        # 全局变量
        self.num = num
        self.min_distance = min_distance
        self.cell_perturb_coefficient = cell_perturb_coefficient

    def run_perturb(self, init_model_path):
        init_model = read(init_model_path)
        structures = []
        for _ in tqdm(range(self.num), desc="Perturb Structure"):
            structures.append(self.perturb(init_model))
        write("./perturb.xyz", structures)
        sysprint("生成完毕!")

    def perturb(self, frame):
        atoms = frame.copy()
        # 位置
        positions = atoms.get_positions()
        # 添加随机微扰
        perturbed_positions = positions + np.random.uniform(
            low=-self.min_distance,
            high=self.min_distance,
            size=positions.shape
        )
        # 更新结构的原子位置
        atoms.set_positions(perturbed_positions)
        # 晶胞微扰
        strains = np.random.uniform(-self.cell_perturb_coefficient, self.cell_perturb_coefficient,(3, 3))
        cell_new = atoms.cell[:] * (1 + strains)
        atoms.set_cell(cell_new, scale_atoms=True)
        return atoms




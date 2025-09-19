#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：select.py
@Author ：RongYi
@Date ：2025/5/9 17:54
@E-mail ：2071914258@qq.com
"""
import os
import random

import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from pynep.calculate import NEP
from pynep.select import FarthestPointSample
from ase.io import read, write
from auto_nep.utils.filter_structure import Filter_structure
from auto_nep.sysprint import sysprint


class Select:
    def __init__(self, trajectory_path, max, min_distance, nep, filter):
        self.trajectory_path = trajectory_path
        self.filter = filter
        self.max = int(max)
        self.min_distance = min_distance
        self.nep = nep

    def run_select(self):
        sysprint("[select] select structures.")
        if self.filter:
            filter_structure = Filter_structure()
            atoms = filter_structure.run_filter(self.trajectory_path, self.filter)
        else:
            atoms = read(self.trajectory_path, index=":")

        calc = NEP(model_file=self.nep)
        # calculate descriptors and latent descriptors
        des = np.array([np.mean(calc.get_descriptor(frame), axis=0) for frame in atoms])
        sampler = FarthestPointSample(min_distance=self.min_distance)
        selected_i = sampler.select(des, [])

        if len(selected_i) > self.max:
            sysprint(f"[select] {len(selected_i)} > {self.max}. Random select {self.max} structures.")
            random.shuffle(selected_i)
            selected_i = selected_i[:self.max]
        write("selected.xyz", [atoms[i] for i in selected_i])
        sysprint(f"[select] {len(selected_i)} structures. Write selected.xyz and select.png.")

        reducer = PCA(n_components=2)
        reducer.fit(des)
        proj = reducer.transform(des)
        plt.scatter(proj[:, 0], proj[:, 1], label="all data")
        selected_proj = reducer.transform(np.array([des[i] for i in selected_i]))
        plt.scatter(selected_proj[:, 0], selected_proj[:, 1], label="selected data")
        plt.legend()
        plt.savefig("select.png")


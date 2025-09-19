#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：check.py
@Author ：RongYi
@Date ：2025/5/2 16:22
@E-mail ：2071914258@qq.com
"""
import os
import shutil
from auto_nep.sysprint import sysprint


def check(config):
    # 通用文件/文件夹检测
    if os.path.exists("./gpumd-dataset") and not config["active"]["restart"]:
        sysprint(f"Warning: 主动学习期间将清空 gpumd-datase 文件夹!(保留文件)", "red")
        while True:
            user_input = input("=========== 输入 yes 继续 输入 no 退出 ===========\n")
            if user_input == "yes":
                for item in os.listdir("./gpumd-dataset"):
                    if os.path.isdir(f"./gpumd-dataset/{item}"):
                        shutil.rmtree(f"./gpumd-dataset/{item}")
                break
            elif user_input == "no":
                exit()
            else:
                continue

    # active 检测 需要初始势函数和训练集
    if config["task_type"] == "active":
        if not os.path.exists(config["active"]["init_nep_txt"]):
            sysprint(f'未找到 {config["active"]["init_nep_txt"]} 请检查配置文件', "red")
            exit()
        if not os.path.exists(config["active"]["init_train_xyz"]):
            sysprint(f'未找到 {config["active"]["init_train_xyz"]} 请检查配置文件', "red")
            exit()
        if not os.path.exists(config["active"]["model_dir"]):
            sysprint(f'未找到 {config["active"]["model_dir"]} 请检查配置文件', "red")
            exit()
        if not os.path.exists(config["abacus"]["abacus_pbs_path"]):
            sysprint(f'未找到 {config["active"]["abacus_pbs_path"]} 请检查配置文件', 'red')
            exit()
        if not os.path.exists(config["abacus"]["abacus_input_path"]):
            sysprint(f'未找到 {config["active"]["abacus_input_path"]} 请检查配置文件', 'red')
            exit()
        if not os.path.exists(config["active"]["run_in_path"]):
            sysprint(f'未找到 {config["active"]["run_in_path"]} 请检查配置文件', 'red')
            exit()
        if config["active"]["restart"]:
            if not os.path.exists(config["active"]["nep_restart"]):
                sysprint(f'未找到 {config["active"]["nep_restart"]} 请检查配置文件', 'red')
                exit()
        if not os.path.exists(config["active"]["gpumd_pbs_path"]):
            sysprint(f'未找到 {config["active"]["gpumd_pbs_path"]} 请检查配置文件', 'red')
            exit()
        if not os.path.exists(config["active"]["nep_pbs_path"]):
            sysprint(f'未找到 {config["active"]["nep_pbs_path"]} 请检查配置文件', 'red')
            exit()
        if config["active"]["max_structures_per_model"] is None:
            sysprint(f'未设置 max_structures_per_model 请检查配置文件', 'red')
            exit()



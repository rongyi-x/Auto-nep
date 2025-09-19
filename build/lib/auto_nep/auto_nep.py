#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：auto_nep.py
@Author ：RongYi
@Date ：2025/5/4 12:02
@E-mail ：2071914258@qq.com
"""
import os.path
import re
import shutil
import time
import random
from ase.io import read, write
from auto_nep.sysprint import sysprint
from auto_nep.check import check
from auto_nep.select import select_active, select_extend
from auto_nep.abacus import Abacus
from auto_nep.shift import shift_energy


class Auto_nep():
    """
    整体框架 auto_nep
    使用 auto-nep train train.yaml 命令 -> Auto_nep.run()
    """
    def __init__(self, config):
        self.home_path = os.getcwd()
        self.config = config
        # 将所有路径变成绝对路径
        self.nep_in = self.config["active"]["nep_in_path"] = os.path.abspath(self.config["active"]["nep_in_path"])
        self.init_nep_txt = self.config["active"]["init_nep_txt"] = os.path.abspath(self.config["active"]["init_nep_txt"])
        self.init_train_xyz = self.config["active"]["init_train_xyz"] = os.path.abspath(self.config["active"]["init_train_xyz"])
        self.model_dir = self.config["active"]["model_dir"] = os.path.abspath(self.config["active"]["model_dir"])
        self.run_in = self.config["active"]["run_in_path"] = os.path.abspath(self.config["active"]["run_in_path"])
        self.input = self.config["abacus"]["abacus_input_path"] = os.path.abspath(self.config["abacus"]["abacus_input_path"])
        self.pbs = self.config["abacus"]["abacus_pbs_path"] = os.path.abspath(self.config["abacus"]["abacus_pbs_path"])
        self.pp = self.config["abacus"]["pp_path"] = os.path.abspath(self.config["abacus"]["pp_path"])
        self.basis = self.config["abacus"]["basis_path"] = os.path.abspath(self.config["abacus"]["basis_path"])
        self.gpumd_pbs = self.config["active"]["gpumd_pbs_path"] = os.path.abspath(self.config["active"]["gpumd_pbs_path"])
        self.nep_pbs = self.config["active"]["nep_pbs_path"] = os.path.abspath(self.config["active"]["nep_pbs_path"])

        self.restart = config["active"]["restart"]
        if self.restart:
            self.nep_restart = self.config["active"]["nep_restart"] = os.path.abspath(self.config["active"]["nep_restart"])

        self.task_type = self.config["task_type"]
        self.max_iterations = self.config["active"]["max_iterations"]
        self.max_structures_per_iteration = self.config["active"]["max_structures_per_iteration"]
        self.max_structures_per_model = self.config["active"]["max_structures_per_model"]
        self.shift_energy = self.config["active"]["shift_energy"]
        self.nep = self.config["active"]["nep_path"]
        self.gpumd = self.config["active"]["gpumd_path"]

    def print(self, content, color="white"):
        sysprint(content, color)

    def check(self):
        check(self.config)

    def run(self):
        # 1-检测
        self.check()
        # 2-读取任务类型
        if self.task_type == "abacus":
            # 微扰数据集 -> abacus -> nep -> active
            pass
        if self.task_type == "active":
            # nep, train.xyz -> select -> gpumd -> scf -> nep -> select -> gpumd ...
            # 迭代循环 结束判断
            iter_num = 0
            while iter_num < self.max_iterations:
                t1 = time.time()
                self.print(f"==================== 主动学习第 {iter_num} 次迭代开始 ====================")
                if self.iter(iter_num) == 0:
                    self.print("主动学习完成!", "red")
                    break
                t2 = time.time()
                self.print(f"[nep-v{iter_num}] 迭代完成 Spend time: {int((t2 - t1))/60} minutes")
                iter_num += 1

    def iter(self, iter_num):
        # 单次迭代逻辑设计
        iter_dir = self.home_path+f"/gpumd-dataset/iter_{iter_num}"
        os.makedirs(iter_dir, exist_ok=True)
        os.chdir(iter_dir)

        self.run_scf(iter_num)
        self.run_nep(iter_num)
        self.select_active_set(iter_num)
        self.run_gpumd(iter_num)
        if os.path.getsize("./4-gpumd/large_gamma.xyz") == 0:
            return 0

        to_add = self.select_structures(iter_num)
        self.print(f"[Step1] 选择 {len(to_add)} 个结构")
        if len(to_add) > self.max_structures_per_iteration:
            self.print(f"[Step2] 最大结构个数 {self.max_structures_per_iteration}")
            random.seed(10)
            random.shuffle(to_add)
            to_add = to_add[: self.max_structures_per_iteration]
        write(f"{iter_dir+'/5-select_structures/to_add.xyz'}", to_add)

        return 1

    def run_scf(self, iter_num):
        self.print(f"[nep-v{iter_num}] 1-SCF")
        os.makedirs("1-scf", exist_ok=True)
        os.chdir("1-scf")

        if self.restart and os.path.exists("./DONE"):
            self.print("[续算模式] 任务已完成")
            os.chdir("..")
            return None

        if iter_num == 0:
            os.system(f"cat {self.init_train_xyz} > ./train.xyz")
        else:
            abacus = Abacus(self.config, f"../../iter_{iter_num-1}/5-select_structures/to_add.xyz")
            abacus.run("to_add.xyz")
            os.remove("ase_sort.dat")
        with open("./DONE", "w") as f:
            f.close()
        os.chdir("..")

    def run_nep(self, iter_num):
        self.print(f"[nep-v{iter_num}] 2-NEP")
        os.makedirs("2-nep", exist_ok=True)
        os.chdir("2-nep")

        if self.restart and os.path.exists("./DONE"):
            self.print("[续算模式] 任务已完成")
            os.chdir("..")
            return None

        if self.shift_energy:
            # 能量平移生成平移过后的 train.xyz
            self.print("[Step1] 能量平移")
            if iter_num == 0:
                os.system(f"cat {self.init_train_xyz} > v0-no-shifted.xyz")
                shift_energy(f"v0-no-shifted.xyz", "train.xyz")
                os.system(f"cat {self.init_nep_txt} > nep.txt")
                os.system(f"cat {self.nep_restart} > nep.restart")
                with open("DONE", "w") as f:
                    f.close()
                os.chdir("..")
                return None
            else:
                os.system(f"cat ../../iter_{iter_num-1}/2-nep/v{iter_num-1}-no-shifted.xyz"
                          f" ../1-scf/to_add.xyz > v{iter_num}-no-shifted.xyz")
                shift_energy(f"v{iter_num}-no-shifted.xyz", "train.xyz")  # train.xyz
        else:
            # 不平移
            if iter_num == 0:
                os.system(f"cat {self.init_train_xyz} > train.xyz")
                os.system(f"cat {self.init_nep_txt} > nep.txt")
                os.system(f"cat {self.nep_restart} > nep.restart")
                with open("DONE", "w") as f:
                    f.close()
                os.chdir("..")
                return None
            else:
                os.system(f"cat ../../iter_{iter_num - 1}/2-nep/train.xyz"
                          f" ../1-scf/to_add.xyz > train.xyz")  # train.xyz

        # 平移只影响 train.xyz 产生
        os.system(f"cat ../../iter_{iter_num - 1}/2-nep/nep.txt > nep.txt")  # nep.txt
        os.system(f"cat ../../iter_{iter_num - 1}/2-nep/nep.restart > nep.restart")  # nep.restart
        os.system(f"cat {self.nep_in} > nep.in")  # nep.in
        os.system(f"cat {self.nep_pbs} > nep.pbs")  # nep.pbs
        self.print("[Step2] nep-train")
        os.system("qsub nep.pbs")  # 提交任务

        # 任务完成检测 pbs 脚本完成后会生成 DONE 文件
        time1 = time.perf_counter()
        flag = True
        times = 0
        while flag:
            for root, _, files in os.walk("./"):
                if "DONE" in files:
                    flag = False
                else:
                    if times % 60 == 0:
                        spend_time = time.perf_counter() - time1
                        h = spend_time // 3600
                        m = (spend_time // 60) % 60
                        s = spend_time % 60
                        self.print(f"[nep-v{iter_num}] Train spend time: {h:.0f}h {m:.0f}m {s:.0f}s")
                        time.sleep(10)
                        times += 1
                    times += 1
        os.chdir("..")

    def select_active_set(self, iter_num):
        self.print(f"[nep-v{iter_num}] 3-select active set")
        os.makedirs("3-select_active_set", exist_ok=True)
        os.chdir("3-select_active_set")

        if self.restart and os.path.exists("./DONE"):
            self.print("[续算模式] 任务已完成")
            os.chdir("..")
            return None

        shutil.copy("../2-nep/train.xyz", "./")
        shutil.copy("../2-nep/nep.txt", "./")
        select_active("./train.xyz", "./nep.txt", os.getcwd())
        os.remove("./train.xyz")
        os.remove("./nep.txt")

        with open("./DONE", "w") as f:
            f.close()
        os.chdir("..")

    def run_gpumd(self, iter_num):
        self.print(f"[nep-v{iter_num}] 4-GPUMD")
        os.makedirs("4-gpumd", exist_ok=True)
        os.chdir("4-gpumd")
        shutil.copy("../3-select_active_set/active_set.asi", "./")
        task_num = 0
        for stru in os.listdir(self.model_dir):
            os.makedirs(f"{stru}", exist_ok=True)
            os.chdir(f"{stru}")

            if self.restart and os.path.exists("./DONE"):
                self.print(f"[续算模式] 任务{stru}已完成")
                os.chdir("..")
                task_num += 1
                continue
            os.system(f"cat {self.model_dir}/{stru} > ./model.xyz")  # model.xyz
            os.system(f"cat {self.run_in} > ./run.in")  # run.in
            os.system(f"cat ../../2-nep/nep.txt > ./nep.txt")  # nep.txt
            os.system(f"cat {self.gpumd_pbs} > ./gpumd.pbs")  # gpumd.pbs
            os.system("qsub gpumd.pbs")  # 提交
            os.chdir("..")
            task_num += 1
        self.check_gpumd(task_num, iter_num)
        # 每个结构的任务个数检测 extrapolation_dump.xyz
        self.check_struc_num()
        os.system("cat */extrapolation_dump.xyz > ./large_gamma.xyz")
        os.chdir("..")


    def select_structures(self, iter_num):
        self.print(f"[nep-v{iter_num}] 5-select structures")
        os.makedirs("5-select_structures", exist_ok=True)
        os.chdir("5-select_structures")

        if self.restart and os.path.exists("DONE"):
            self.print("[续算模式] 任务已完成")
            ret = read("./to_add.xyz", index=":")
            os.chdir("..")
            return ret

        shutil.copy("../2-nep/train.xyz", ".")
        shutil.copy("../2-nep/nep.txt", ".")
        shutil.copy("../4-gpumd/large_gamma.xyz", ".")
        select_extend()
        with open("./DONE", "w") as f:
            f.close()
        ret = read("./to_add.xyz", index=":")
        os.chdir("..")
        return ret

    def check_gpumd(self, task_num, iter_num):
        sysprint(f"[nep-v{iter_num}] Check GPUMD")

        start_time = time.perf_counter()
        total_time = 0  # 计算总耗时 min

        while True:
            accomplish = []
            calculating = []
            awating = []
            for root, _, files in os.walk("./"):
                if "DONE" in files:
                    accomplish.append(root)
                elif "out.log" in files and "DONE" not in files:
                    calculating.append(root)
                elif "gpumd.pbs" in files and "out.log" not in files and "DONE" not in files:
                    awating.append(root)

            if total_time % 6 == 0:
                # Current Task 打印模块
                sysprint("\n-------------------------------- GPUMD -------------------------------\n"
                         f'Total task num: {task_num}\t'
                         f'Total time(s): {round(time.perf_counter() - start_time, 2)}\t'
                         f"  Progress:{len(accomplish)}/{task_num}\n"
                         f"-----------------------------------------------------------------------")
                for task in calculating:
                    step = self.get_step(task)
                    print(f"Current Task: [{task}] Step: [{step}]\n"
                          f"-----------------------------------------------------------------------")

            if len(accomplish) == task_num:
                sysprint("计算完成提取 larger_gamma.xyz", 'red')
                sysprint(f"Mean time(s):{(time.perf_counter() - start_time) / len(accomplish): .2f} s")
                break

            total_time += 1
            time.sleep(10)

    def get_step(self, task):
        try:
            with open(task+"/neighbor.out") as f:
                content = f.readlines()
            match = re.search("step (\d+)", content[-1])
            return match.group()
        except:
            return 0

    def check_struc_num(self):
        """
        检测当前目录下的 extrapolation_dump.xyz 个数
        :return:
        """
        for roots, _, files in os.walk("."):
            if "extrapolation_dump.xyz" in files:
                extrapolation = read(roots + "/extrapolation_dump.xyz", index=":", format="extxyz")
                if len(extrapolation) > self.max_structures_per_model:
                    sysprint(f"[Warning] 探索到 {len(extrapolation)} 结构, 随机选取 {self.max_structures_per_model} 结构")
                    random.shuffle(extrapolation)
                    extrapolation = extrapolation[: self.max_structures_per_model]
                    write(roots + "/extrapolation_dump.xyz", extrapolation, format="extxyz""")


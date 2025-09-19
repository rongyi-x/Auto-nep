#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：abacus.py
@Author ：RongYi
@Date ：2025/5/4 16:53
@E-mail ：2071914258@qq.com
"""
import os
import re
import shutil
import time

from ase.io import read
from tqdm import tqdm

from auto_nep.sysprint import sysprint


class Abacus():
    def __init__(self, config=None, xyz_path="."):
        self.config = config
        self.xyz_path = xyz_path
        self.dataset_roots = []

    def run(self, filename: str):
        self.xyz2abacus()
        self.sub_abacus()
        self.check_abacus()
        self.abacus2nep(filename)
    
    def find_pp_basis(self):
        """
        寻找基组赝势文件
        :param config:
        :return:
        """
        pp, basis = {}, {}

        for index, element_type in enumerate(self.config['element_type']):
            pp_flag, basis_flag = False, False  # 标志位
            # pp_pattern: 以元素类型开头, 以.upf结尾
            pp_pattern = rf'^{element_type}[._].*upf$'
            # basis_pattern: 以元素类型开头, 以.orb结尾
            basis_pattern = rf'^{element_type}[._].*orb$'

            for filename in os.listdir(self.config["abacus"]["pp_path"]):
                if re.match(pp_pattern, filename):
                    pp[f'{element_type}'] = filename
                    pp_flag = True
                    break

            for filename in os.listdir(self.config["abacus"]["basis_path"]):
                if re.match(basis_pattern, filename):
                    basis[f'{element_type}'] = filename
                    basis_flag = True
                    break

            if pp_flag is False:
                sysprint(f'未找到 {element_type} 赝势文件, 请检查 {self.config["abacus"]["pp_path"]}', 'red')
                exit()
            if basis_flag is False:
                sysprint(f'未找到 {element_type} 轨道文件, 请检查 {self.config["abacus"]["basis_path"]}', 'red')
                exit()
        sysprint(f'赝势文件: {pp}', 'yellow')
        sysprint(f'轨道文件: {basis}', 'yellow')
        return pp, basis
    
    def xyz2abacus(self):
        """
        制作 abacus 训练集
        :param config: 训练配置
        :return: 数据集路径
        """
        # 自动生成 abacus dataset
        home_path = os.getcwd()
        atoms = read(self.xyz_path, index=":")
        # 寻找赝势文件和轨道文件
        pp, basis = self.find_pp_basis()
        sysprint(f'abacus_dataset 训练集大小: {len(atoms)}')
        for i in range(1, len(atoms) + 1):
            single_struc = read(self.xyz_path, index=f'{i-1}')
            os.makedirs(f'./{i}', exist_ok=True)
            single_struc.write(f'./{i}/STRU', format='abacus', pp=pp,
                        basis=basis)
            self.dataset_roots.append(home_path+f'/{i}')

    def sub_abacus(self):
        """
        提交任务脚本
        :param config: 配置文件
        :return:
        """

        # 提交任务: 收敛标准 time.json文件
        task_num = 0
        home_path = os.getcwd()
        
        for root in self.dataset_roots:
            if not os.path.exists(root + "/time.json"):
                shutil.copy(self.config["abacus"]["abacus_input_path"], root)
                shutil.copy(self.config["abacus"]["abacus_pbs_path"], root)
                os.chdir(root)
                os.system('qsub abacus.pbs')
                task_num += 1
        # 提交完成后退回主目录
        os.chdir(home_path)
        sysprint(f'任务提交完成 提交计算任务: {task_num}')


    def spend_time(self, task_path):
        """
        读取当前任务所花费时间
        :param task_path: 任务路径
        :return: step time: h m s
        """
        with open(task_path + "/out.log", encoding='utf-8') as f:
            content = f.read()
            time_pattern = re.compile(r" CU\d+\s+.*\s+(\d+\.\d+)$", re.MULTILINE)
            time_match = time_pattern.findall(content)
            spend_time = 0
            for time in time_match:
                spend_time += float(time)
            step_pattern = re.compile(r" CU\d+\s+.*\s+\d+\.\d+$", re.MULTILINE)
            step_match = step_pattern.findall(content)
            try:
                return step_match[-1], str(int(spend_time // 3600)), str(int(spend_time // 60 % 60)), str(
                    round(spend_time % 60))
            except:
                return None, str(int(spend_time // 3600)), str(int(spend_time // 60 % 60)), str(
                    round(spend_time % 60))

    def check_abacus(self):
        """
        检测任务是否完成
        1.有 out.log 无 time.json 计算中
        2.有 time.json 计算完成r
        3. 无 out.log 无 time.json 等待中
        :return:
        """
        start_time = time.perf_counter()
        total_time = 0  # 计算总耗时 min

        # 处理未计算任务
        warn_times = 1
        while True:
            accomplish = []
            calculating = []
            awating = []
            for root in self.dataset_roots:
                time_json = root + "/time.json"
                out_log = root + f'/out.log'
                if os.path.isfile(time_json):
                    accomplish.append(root)
                elif os.path.isfile(out_log):
                    calculating.append(root)
                else:
                    awating.append(root)

            if total_time % 6 == 0:
                # Current Task 打印模块
                sysprint("\n-------------------------------- abacus -------------------------------\n"
                        f'Total task num: {len(self.dataset_roots)}\t'
                         f'Total time(s): {round(time.perf_counter() - start_time, 2)}\t'
                         f"  Progress:{len(accomplish)}/{len(self.dataset_roots)}\n"
                        f"-----------------------------------------------------------------------")
                for task in calculating:
                    step, h, m, s = self.spend_time(task)
                    print(f"Current Task: [{task}] Spend Time: [{h}h {m}m {s}s]\n"
                          f"Step: [{step}]\n"
                          f"-----------------------------------------------------------------------")

            if len(accomplish) == len(self.dataset_roots):
                sysprint("计算完成提取 nep 训练集 train.xyz", 'red')
                sysprint(f"Mean time(s):{(time.perf_counter() - start_time) / len(accomplish): .2f} s")
                break

            # if len(calculating) == 0 and len(awating) > 0:
            #     sysprint(f"Warning {warn_times}: 以下任务未进行计算!", "red")
            #     for task in awating:
            #         print(f"{task}")
            #     warn_times += 1
            #     if warn_times > self.config["abacus"]["warn_times"]:
            #         # 警告超过三次 自动退出
            #         exit()

            total_time += 1
            time.sleep(10)

    def abacus2nep(self, filename="train.xyz"):
        """
        abacus 训练集 -> nep 训练集
        """
        sysprint("正在生成 nep 训练 trian.xyz 文件")

        log_files = []
        for root in self.dataset_roots:
            for root2, _, files in os.walk(root):
                for file in files:
                    if file == "running_scf.log":
                        log_files.append(os.path.abspath(os.path.join(root2, file)))

        for log_file in tqdm(log_files):
            with open(log_file, encoding='utf-8') as f:
                content = f.read()
            if "charge density convergence is achieved" not in content:
                sysprint(f"任务未收敛: {log_file}", "red")
                continue

            # config_type 训练集位置 windows 和 linux 不同
            if os.name == "nt":
                # Windows
                config_type = log_file.split("\\")[:-2]
                config_type = "\\".join(config_type)
            elif os.name == "posix":
                # Linux
                config_type = log_file.split("/")[:-2]
                config_type = "/".join(config_type)

            # 提取原子总数
            total_atom_number_match = re.search(r"TOTAL ATOM NUMBER = (\d+)", content)
            if total_atom_number_match:
                total_atom_number = total_atom_number_match.group(1)
            else:
                sysprint(f"{log_file} 能量无法提取!", "red")
                continue

            # 提取晶格常数
            lattice_match = re.search(r" Lattice vectors.*(\n.*\n.*\n.*)", content)
            if lattice_match:
                lattice = lattice_match.group(1).strip().replace('+', '')
                lattice = ' '.join([f'{float(l):.10f}' for l in lattice.split()])
            else:
                sysprint(f'{log_file} 晶格常数无法提取!', "red")
                continue

            # 提取能量
            energy_match = re.search(r"FINAL_ETOT_IS\s+(\S+)", content)
            if energy_match:
                energy = float(energy_match.group(1))
            else:
                sysprint(f'{log_file} 能量无法提取!', 'red')
                continue

            # 提取体积
            volume_match = re.search(r"Volume \(A\^3\) = (\S+)", content)
            volume = float(volume_match.group(1).strip())

            # stress 单位转换: kbar -> ev/A^3 正压负拉 -> 负拉正压
            stress_match = re.search(r"TOTAL-STRESS.*\n.*(\n.*\n.*\n.*)", content)
            if stress_match:
                stress = stress_match.group(1).strip()
                # stress = ' '.join([f'{-float(s) * 0.0062415091:.10f}' for s in stress.split()])
                virial = ' '.join([f'{volume * float(s) * 0.062415091:.10f}' for s in stress.split()])

            else:
                sysprint(f'{log_file} 压力无法提取!", "red')
                continue

            # 位置和力 分数坐标 -> 笛卡尔坐标
            # 读取 a b c
            cell_a_match = re.search(r"NORM_A\s+\S+ (.*)", content)
            cell_b_match = re.search(r"NORM_B\s+\S+ (.*)", content)
            cell_c_match = re.search(r"NORM_C\s+\S+ (.*)", content)

            cell_a = float(cell_a_match.group(1))
            cell_b = float(cell_b_match.group(1))
            cell_c = float(cell_c_match.group(1))

            # 元素类型和坐标转换
            type_position_match = re.compile(r"taud_([a-z,A-z]+)\w+\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")
            type_position = type_position_match.findall(content)
            type_position = [f'{type}\t{float(x) * cell_a:.10f}\t{float(y) * cell_b:.10f}\t{float(z) * cell_c:.10f}' for
                             type, x, y, z in type_position]
            # 力 找到TOTAL-FORCE开头后面,所有这类格式的行
            force_match = re.compile(
                r"TOTAL-FORCE \(eV/Angstrom\)\s*"
                r"------------------------------------------------------------------------------------------\s*"
                r"((?:\s*\S+\s+-?\d+\.\d+\s+-?\d+\.\d+\s+-?\d+\.\d+\s*\n)*)",
                re.DOTALL
            )
            force = force_match.search(content).group(1)
            force = list(filter(None, force.split('\n')))
            # 输出文件
            with open(filename, 'a', encoding='utf-8') as f:
                # Stress 表头
                # f.write(f'{total_atom_number}\n'
                #         f'Energy={energy:.10f} Lattice=\"{lattice}\" Stress=\"{stress}\"'
                #         f' Config_type=\"{config_type}\" Properties=species:S:1:pos:R:3:forces:R:3'
                #         f' Weight=1.0 Pbc=\"T T T\"\n')

                # virial 表头
                f.write(f'{total_atom_number}\n'
                        f'Energy={energy:.10f} Lattice=\"{lattice}\" Virial=\"{virial}\"'
                        f' Config_type=\"{config_type}\" Properties=species:S:1:pos:R:3:forces:R:3'
                        f' Weight=1.0 Pbc=\"T T T\"\n')

                # 元素种类 位置 力
                for part1, part2 in zip(type_position, force):
                    part2 = part2.split(' ')
                    # 定义正则表达式模式，匹配整数和浮点数
                    pattern = re.compile(r'^[+-]?\d+(\.\d+)?$')
                    # 使用列表推导式过滤非数字元素
                    part2 = [item for item in part2 if pattern.match(item)]
                    part2 = '\t'.join(part2)

                    part = '\t'.join([part1, part2])
                    f.write(part + "\n")
        

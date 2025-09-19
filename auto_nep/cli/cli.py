#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：automation_nep
@File ：cli.py
@Author ：RongYi
@Date ：2025/4/29 14:31
@E-mail ：2071914258@qq.com
"""
import argparse
import os.path

from auto_nep.shift import shift_energy
from auto_nep.auto_nep import Auto_nep  # 类
from auto_nep.abacus import Abacus  # 类
from auto_nep.utils import Perturb, Select  # 类
from auto_nep.utils.config import load_config
from auto_nep.utils import find_struc, convert_format
from auto_nep.sysprint import sysprint


def build_train(subparsers):
    # 添加 train 子命令
    train_parser = subparsers.add_parser("train",
                                         help="Run training.")
    # 为 train 添加子命令 yaml 配置文件
    train_parser.add_argument("-y", "--yaml",
                              type=str,
                              default="train.yaml",
                              help="Train config file yaml path, default is train.yaml.")


def build_abacus2nep(subparsers):
    # 添加 abacus2nep 命令
    abacus2nep = subparsers.add_parser("abacus2nep",
                                       help="Convert abacus dataset to nep train.xyz.")
    # 添加子命令 path
    abacus2nep.add_argument("-d", "--dataset",
                            help="Abacus dataset path.")


def build_perturb(subparsers):
    # 添加 perturb 命令
    abacus2nep = subparsers.add_parser("perturb",
                                       help="Perturb structure.")
    # 添加子命令 path
    abacus2nep.add_argument("-m", "--model",
                            type=str,
                            help="Init model path.")
    # 添加子命令 num
    abacus2nep.add_argument("-n", "-num",
                            type=int,
                            default=40,
                            help="Number of perturb structures, default is 40.")
    # 添加子命令 cell_coefficient
    abacus2nep.add_argument("-c", "-cell_coefficient",
                            type=float,
                            default=0.05,
                            help="Cell perturb coefficient, default is 0.05.")
    # 添加子命令 distance
    abacus2nep.add_argument("-d", "-distance",
                            type=float,
                            default=0.2,
                            help="Atoms movement distance, default is 0.2.")

def build_select(subparsers):
    # 添加 select 命令
    select = subparsers.add_parser("select",
                                   help="Select structure.")
    # 添加子命令 path
    select.add_argument("-t", "--trajectory",
                        help="Trajectory path.")
    # 添加子命令 max
    select.add_argument("-m", "-max",
                        type=str,
                        default=20,
                        help="Maximum number of structures to select, default is 20.")
    # 添加子命令 min_distance
    select.add_argument("-d", "--min_distance",
                        type=float,
                        default=0.01,
                        help="Minimum bond length for farthest-point sampling, default is 0.01.")
    # 添加子命令 nep
    select.add_argument("-nep", "--nep",
                        type=str,
                        default="nep.txt",
                        help="Nep potential file, default is nep.txt.")
    # 添加子命令 filter
    select.add_argument("-f", "--filter",
                        type=float,
                        const=0.7,
                        nargs='?',
                        help="Whether to filter based on covalent radius, the default is False."
                             " If True, the default coefficient is 0.7, and a coefficient can be passed in",
                        default=False)


def build_shift(subparsers):
    # 添加 shift 命令
    shift = subparsers.add_parser("shift",
                                  help="Shift energy.")
    # 添加子命令
    shift.add_argument("-in", "--input",
                       help="Input file path.")
    shift.add_argument("-out", "--output",
                       help="Output file path.",
                       default="./train.xyz")

def build_find_from_dataset(subparsers):
    # 添加 find命令
    shift = subparsers.add_parser("find",
                                  help="Find your structure from a larger dataset.After you delete "
                                       "the structure, you need to select these structures from the "
                                       "dataset before the energy translation.")

    shift.add_argument("-md", "--my_dataset",
                       help="My dataset path.")

    shift.add_argument("-d", "--dataset",
                       help="No shifted energy dataset path.")


def build_convert_format(subparsers):
    """
    格式转换脚本 xyz -> abacus
    :param subparspers:
    :return:
    """
    # 添加 convert 命令
    shift = subparsers.add_parser("convert",
                                  help="Convert format from xyz to abacus(STRU)")

    shift.add_argument("-xyz",
                       help="xyz file root.")



def main():
    """
    命令行参数设置
    :return:
    """
    parser = argparse.ArgumentParser(description="Automation NEP CLI")
    subparsers = parser.add_subparsers(dest="command")

    build_train(subparsers)
    build_abacus2nep(subparsers)
    build_perturb(subparsers)
    build_select(subparsers)
    build_shift(subparsers)
    build_find_from_dataset(subparsers)
    build_convert_format(subparsers)

    home_folder = os.path.expanduser("~")
    env_file_path = os.path.join(home_folder, ".auto_nep_env")

    if not os.path.exists(env_file_path):
        with open(env_file_path, "w") as f:
            f.write("pp_path=\n")
            f.write("basis_path=\n")
        print("创建环境成功")

    args = parser.parse_args()
    if args.command == "train":
        config_path = args.yaml
        config = load_config(config_path)
        a = Auto_nep(config)
        a.run()
    elif args.command == "abacus2nep":
        abacus = Abacus()
        abacus.dataset_roots = [f"{args.dataset}"]
        sysprint(f"从 {args.dataset} 提取 train.xyz")
        abacus.abacus2nep()
    elif args.command == "perturb":
        if args.path is None:
            sysprint("请输入初始模型的路径 -path", "red")
            exit()
        perturb = Perturb(args.num, args.distance, args.cell_coefficient)
        perturb.run_perturb(f"{args.path}")
    elif args.command == "select":
        if args.path is None:
            sysprint("请输入 trajectory 的路径 -path", "red")
            exit()
        select = Select(args.path, args.max, args.min_distance, args.nep, args.filter)
        select.run_select()
    elif args.command == "shift":
        if args.input is None:
            sysprint("请输入 input 的路径 -in", "red")
            exit()
        shift_energy(f"{args.input}", f"{args.output}")
    elif args.command == "find":
        if args.my_dataset is None:
            sysprint("请输入 my_dataset 的路径 -md", "red")
            exit()
        if args.dataset is None:
            sysprint("请输入 dataset 的路径 -d", "red")
            exit()
        find_struc(f"{args.my_dataset}", f"{args.dataset}")
    elif args.command == "convert":
        if args.xyz is None:
            sysprint("请输入 xyz 的路径 -xyz", "red")
            exit()
        convert_format(args.xyz)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

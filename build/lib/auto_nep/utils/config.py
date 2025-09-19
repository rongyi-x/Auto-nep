#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：automation_nep
@File ：config.py
@Author ：RongYi
@Date ：2025/4/29 16:07
@E-mail ：2071914258@qq.com
"""
import yaml


def load_config(config_path):
    """
    加载 YAML 配置文件
    :param config_path: YAML 文件路径
    :return: 配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config


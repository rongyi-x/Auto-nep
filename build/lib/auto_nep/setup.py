#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：automation_nep
@File ：setup.py.py
@Author ：RongYi
@Date ：2025/4/29 14:32
@E-mail ：2071914258@qq.com
"""
# setup.py
from setuptools import setup, find_packages

setup(
    name="automation_nep",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'auto-nep=auto_nep.cli.cli:main',  # 更新入口点为 main 函数
        ],
    },
)
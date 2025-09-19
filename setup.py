#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：setup.py.py
@Author ：RongYi
@Date ：2025/5/1 12:53
@E-mail ：2071914258@qq.com
"""
from setuptools import setup, find_packages

setup(
    name="auto-nep",
    version="0.0.15",
    author='Jack-RY',
    author_email='2071914258@qq.com',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'auto-nep = auto_nep.cli.cli:main',
        ],
    },
)

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：MyTools
@File ：get_now_time.py
@Author ：RongYi
@Date ：2025/4/29 10:42
@E-mail ：2071914258@qq.com
"""
from datetime import datetime
from colorama import Fore, Style


def now_time():
    """
    获取当前时间
    :return: 当前时间
    """
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return Fore.CYAN+formatted_time+Style.RESET_ALL


def sysprint(content: str, color='white'):
    if color == 'red':
        return print(f"[{now_time()}] {Fore.RED + content + Style.RESET_ALL}")
    elif color == 'yellow':
        return print(f"[{now_time()}] {Fore.YELLOW + content + Style.RESET_ALL}")
    else:
        return print(f"[{now_time()}] {content}")

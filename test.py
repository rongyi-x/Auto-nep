#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：test.py
@Author ：RongYi
@Date ：2025/5/10 17:53
@E-mail ：2071914258@qq.com
"""

import os
from ase.io import read
from ase import Atom

atoms = read("./phonon.xyz", index=":")
stru = Atom([])
for index, i in enumerate(atoms):
    i.wrap()
    i.write(f"./wraped{index}.xyz")

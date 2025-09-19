#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：select_gamma.py
@Author ：RongYi
@Date ：2025/5/3 16:24
@E-mail ：2071914258@qq.com
"""
from ase.io import write
from pynep.io import load_nep, dump_nep
from tools import get_gamma

nep_file = "nep.txt"
traj = load_nep("to_select.xyz")

get_gamma(traj, nep_file, "active_set.asi")

out_traj = [atoms for atoms in traj if atoms.arrays["gamma"].max() > 1]
try:
    dump_nep("large_gamma.xyz", out_traj)
except:
    write("large_gamma.xyz", out_traj)

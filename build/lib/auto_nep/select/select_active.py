#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：auto_nep
@File ：select_active.py
@Author ：RongYi
@Date ：2025/5/3 11:42
@E-mail ：2071914258@qq.com
"""

from ase.io import write
from pynep.io import load_nep, dump_nep
from auto_nep.select.tools import get_B_projections, get_active_set


def select_active(xyz_path, nep_path, out_dir):
    nep_file = nep_path
    traj = load_nep(xyz_path)

    B_projections, B_projections_struct_index = get_B_projections(traj, nep_file)
    active_set_inv, active_set_struct = get_active_set(
        B_projections, B_projections_struct_index, out_dir=out_dir
    )

    out_traj = [traj[i] for i in active_set_struct]
    try:
        dump_nep(out_dir+"/select_active.xyz", out_traj)
    except:
        write(out_dir+"/select_active.xyz", out_traj)

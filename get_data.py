# -*- coding: utf-8 -*-

import numpy as np
import os
import re


from common_class import CommonClass


def invert_array(a):
    s = np.empty(a.shape)
    for i, v in enumerate(a):
        s[i] = a[a.shape[0]-1-i:a.shape[0]-i:]
    return s


def change_columns(a):
    s = np.empty(a.shape)
    for i, v in enumerate(a):
        s[i] = [v[1], v[2], v[0]]
    return s


def get_unique_array(a):

    temp = []
    u, indices = np.unique(a, return_index=True, axis=0)
    indices.sort()
    for i in indices:
        temp.append(list(a[i]))

    return np.array(temp)


if __name__ == "__main__":

    root_dir = os.getcwd()
    airfoil_sections_dir = r'airfoils'
    airfoil_sections_dir = os.path.join(root_dir, airfoil_sections_dir)
    airfoil_file = os.path.join(airfoil_sections_dir, 'b1', 'airfoil.dat')

    prt_name = 'b1.prt'
    prt_file = os.path.join(airfoil_sections_dir, 'prt', prt_name)

    ps_airfoils_dir = 'ps_airfoils'
    ss_airfoils_dir = 'ss_airfoils'

    ps_airfoils_dir = os.path.join(airfoil_sections_dir, ps_airfoils_dir)
    ss_airfoils_dir = os.path.join(airfoil_sections_dir, ss_airfoils_dir)

    file_operate = CommonClass()

    # Get suction side airfoils files
    is_exist, airfoils_data = file_operate.get_files(ss_airfoils_dir, ('.dat',))

    # Flip suction side coordinates
    if is_exist:
        for ss_airfoils in airfoils_data:
            data = np.genfromtxt(ss_airfoils, delimiter='\t', usecols=(0, 1, 2), dtype=None)
            data = invert_array(data)
            new_file_name = f'revert_{os.path.split(ss_airfoils)[1]}'
            new_file = os.path.join(airfoil_sections_dir, new_file_name)
            np.savetxt(new_file, data, delimiter='\t')

    is_exist, airfoils_data = file_operate.get_files(airfoil_sections_dir, ('.dat',))

    sections = {}

    # Combine PS and SS coordinates
    pattern = re.compile(r'section\d')
    if is_exist:
        for airfoil in airfoils_data:
            file_name = os.path.split(airfoil)[1]
            key = re.search(pattern, file_name)[0]
            data = np.genfromtxt(airfoil, delimiter='\t', usecols=(0, 1, 2), dtype=None)
            if key not in sections.keys():
                sections[key] = data
            else:
                sections[key] = np.vstack((sections[key], data))

    # Flip airfoils coordinates
    for key, val in sections.items():
        sections[key] = change_columns(val)

    if os.path.isfile(airfoil_file):
        os.remove(airfoil_file)

    with open(airfoil_file, 'a') as f:

        for k, v in sections.items():
            f.write(f'{k},,\n')
            v = get_unique_array(v)
            np.savetxt(f, v, delimiter=',')

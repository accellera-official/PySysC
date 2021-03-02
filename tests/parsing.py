#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

from cppyy_backend._cppyy_generator import CppyyGenerator
from  clang.cindex import Config
from pprint import pprint
import glob
import os.path

proj_dir='../../PySysC-SC/components'
flags=['-I/home/eyck/.conan/data/SystemC/2.3.2/minres/stable/package/672f3350f4be793d25afa19a6a77085e20d01ea5/include',
       '-I'+proj_dir,
        '-fvisibility=hidden',
        '-D__PIC__',
        '-Wno-macro-redefined',
        '-std=c++11']
Config.set_library_file('/usr/lib/x86_64-linux-gnu/libclang-6.0.so')
lib = Config().lib
import ctypes
from clang.cindex import Type
items = [
    ("clang_Type_getNumTemplateArguments", [Type], ctypes.c_size_t),
]
for item in items:
    func = getattr(lib, item[0])
    if len(item) >= 2:
        func.argtypes = item[1]

    if len(item) >= 3:
        func.restype = item[2]

    if len(item) == 4:
        func.errcheck = item[3]
g = CppyyGenerator(flags, dump_modules=True, dump_items=True, dump_includes=False, dump_privates=True, verbose=True)
mapping = g.create_mapping([os.path.join(proj_dir, 'initiator.h')])

pprint(mapping)
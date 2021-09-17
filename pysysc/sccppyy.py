#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

import json
import cppyy
import os.path
import site
from pathlib import Path
from sysconfig import get_paths
import sys
import re
import tempfile
import logging
from contextlib import (redirect_stdout, redirect_stderr)
import io
from tqdm.contrib.logging import logging_redirect_tqdm

lang_symbols = {
    3: '199711L',
    11:'201103L',
    14:'201402L',
    17:'201703L'}
lang_level=11

sysIncludeDirs = set()

includeDirs = set()

interactive = False

class NullLogger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.buffer=""

    def __getattr__(self, attr):
        return getattr(self.terminal, attr)
        
    def write(self, message):
        self.buffer+=message
        
def find_file(name, paths):
    for path in paths:
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)
                
def read_config_from_conan(build_dir, build_type='Release'):
    sys.stdout = NullLogger()
    #data = toml.load(os.path.join(build_dir, 'conanbuildinfo.txt'))
    data={}
    with io.open(os.path.join(build_dir, 'conanbuildinfo.txt'), encoding='utf-8') as conan_file:
        sl = conan_file.readlines()
        key=''
        for i, item in enumerate(sl):
            str = item.rstrip()
            match = re.search(r'\[(\S+)\]', str)
            if match:
                key=match.group(1)
                data[key]=[]
            elif len(str):
                data[key].append(str)
                
    # set include pathes and load libraries
    for p in data['includedirs']:
        add_sys_include_path(p)
    for l in data['libdirs']:
        if os.path.exists(l+'/'+'libsystemc.so'):
            cppyy.load_library(l+'/'+'libsystemc.so')
    for b in data['builddirs']:
        if '/systemc/' in b:
            os.environ['SYSTEMC_HOME'] =b
        elif '/systemc-cci/' in b:
            os.environ['CCI_HOME'] = b
        elif '/systemc-scv/' in b:
            os.environ['SCV_HOME'] = b

    msg = sys.stdout.buffer
    sys.stdout=sys.stdout.terminal
    return msg

systemc_loaded=False
cci_loaded=False

def load_systemc():
    if 'SYSTEMC_HOME' in os.environ:
        add_sys_include_path(os.path.join(os.environ['SYSTEMC_HOME'], 'include'))
        for l in ['lib', 'lib64', 'lib-linux', 'lib-linux64']:
            for f in ['libsystemc.so']:
                full_file=os.path.join(os.environ['SYSTEMC_HOME'], l, f)
                if os.path.isfile(full_file):
                    cppyy.load_library(full_file)
                    cppyy.cppdef("""
#define SC_CPLUSPLUS %s
#include "systemc"
#include "tlm"
namespace sc_core { extern void pln(); }
                                """ % lang_symbols[lang_level])
                    systemc_loaded=True
                    _load_systemc_cci()
                    break
            if systemc_loaded: break;
        if not interactive: cppyy.gbl.sc_core.pln()
        cppyy.gbl.sc_core.sc_in_action=True
        _load_pythonization_lib()
        return True
    return False

def _load_systemc_scv():
    if 'SCV_HOME' in os.environ:
        add_sys_include_path(os.path.join(os.environ['SCV_HOME'], 'include'))
        for l in ['lib', 'lib64', 'lib-linux', 'lib-linux64']:
            for f in ['libscv.so']:
                full_file = os.path.join(os.environ['SCV_HOME'], l, f)
                if os.path.isfile(full_file):
                    cppyy.load_library(full_file)
        cppyy.include("cci_configuration")
        cci_loaded=True
        return True
    return False

def _load_systemc_cci():
    for home_dir in ['CCI_HOME', 'SYSTEMC_HOME']:
        if home_dir in os.environ:
            add_sys_include_path(os.path.join(os.environ[home_dir], 'include'))
            for l in ['lib', 'lib64', 'lib-linux', 'lib-linux64']:
                for f in ['libcciapi.so']:
                    full_file = os.path.join(os.environ[home_dir], l, f)
                    if os.path.isfile(full_file):
                        cppyy.load_library(full_file)
            cppyy.include("cci_configuration")
            cci_loaded=True
            return True
    return False

def _load_pythonization_lib(debug = False):
    plat_info = get_paths()
    # check for standard search path
    for key in plat_info:
        plat_dir =plat_info[key]
        if os.path.isdir(plat_dir):
            if debug: logging.debug("Checking for pythonization lib in platform dir %s"%plat_dir)
            for file in os.listdir(plat_dir):
                if re.match(r'pysyscsc.*\.so', file):
                    cppyy.load_library(os.path.join(plat_dir, file))
                    full_path = os.path.join(plat_dir, '../../../include/site/python%d.%d/PySysC/PyScModule.h' % sys.version_info[:2])
                    if debug: logging.debug('found %s, looking for %s'%(file, full_path))
                    if full_path and os.path.isfile(full_path):
                        cppyy.include(full_path)
                    return
    # check site packages first to check for venv
    for site_dir in site.getsitepackages():
        if os.path.isdir(site_dir):
            if debug: logging.debug("Checking for pythonization lib in site package dir %s"%site_dir)
            for file in os.listdir(site_dir):
                if re.match(r'pysyscsc.*\.so', file):
                    cppyy.load_library(os.path.join(site_dir, file))
                    full_path = find_file('PyScModule.h', site.PREFIXES)
                    if debug: logging.debug('found %s, looking at %s for %s'%(file, site.PREFIXES, full_path))
                    if full_path and os.path.isfile(full_path):
                        cppyy.include(full_path)
                    return
    if site.ENABLE_USER_SITE:
        #check user site packages (re.g. ~/.local)
        user_site_dir = site.getusersitepackages()
        if os.path.isdir(user_site_dir):
            if debug: logging.debug("Checking for pythonization lib in user site dir %s"%user_site_dir)
            for file in os.listdir(user_site_dir):
                if re.match(r'pysyscsc.*\.so', file):
                    cppyy.load_library(os.path.join(user_site_dir, file))
                    user_base = site.USER_BASE
                    full_path = user_base + '/include/python%d.%d/PySysC/PyScModule.h' % sys.version_info[:2]
                    if debug: logging.debug('found %s, looking at %s for %s'%(file, user_base, full_path))
                    if os.path.isfile(full_path):
                        cppyy.include(full_path)
                    return
    # could not be found in install, maybe development environment
    pkgDir = os.path.join(os.path.dirname( os.path.realpath(__file__)), '..')
    if os.path.isdir(pkgDir):
        if debug: logging.debug("Checking for pythonization lib in source dir %s"%pkgDir)
        for file in os.listdir(pkgDir):
            if re.match(r'pysyscsc.*\.so', file):
                cppyy.load_library(os.path.join(pkgDir, file))
                full_path = os.path.join(pkgDir, 'PyScModule.h')
                if full_path and os.path.isfile(full_path):
                    cppyy.include(full_path)
                return    
    sys.exit("No Pythonization found")

def add_library(header, lib, project_dir=None):
    lib_path = lib
    if(project_dir is not None):
        for root, dirs, files in os.walk(project_dir):
            if lib in files:
                lib_path = os.path.join(root, lib)
                break
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        cppyy.load_library(lib_path)
        cppyy.include(header)
    return buf.getvalue()
    
def add_include_path(incl):
    includeDirs.add(incl)
    cppyy.add_include_path(incl)

def add_sys_include_path(incl):
    sysIncludeDirs.add(incl)
    cppyy.add_include_path(incl)

# prepare a pythonizor
def _pythonizor(clazz, name):
    # A pythonizor receives the freshly prepared bound C++ class, and a name stripped down to
    # the namespace the pythonizor is applied. Also accessible are clazz.__name__ (for the
    # Python name) and clazz.__cpp_name__ (for the C++ name)
    if name == 'sc_time':
        clazz.__repr__ = lambda self: repr(self.to_string())
        clazz.__str__ = lambda self: self.to_string()
    elif name in ['sc_object', 'sc_module']:
        clazz.__repr__ = lambda self: repr(self.name())
    elif len(name) > 8 and name[:7] == 'sc_port<':
        clazz.__repr__ = lambda self: repr(self.name())
    elif len(name) > 10 and name[:9] == 'sc_export<':
        clazz.__repr__ = lambda self: repr(self.name())

# install the pythonizor as a callback on namespace 'Math' (default is the global namespace)
cppyy.py.add_pythonization(_pythonizor, 'sc_core')
    
# reflection methods
def get_members(sc_object):
    def is_cpp_data_type(name, module):
        matches =  [x for x in ['int', 'char', 'float', 'double'] if name == x]
        if len(matches) > 0 or module[:10] == "cppyy.gbl.":
            return True
        else:
            return False

    members = [(e, getattr(sc_object, e)) for e in dir(sc_object)]
    return [(k,v) for k,v in members if is_cpp_data_type(type(v).__name__, type(v).__module__)]

def get_methods(sc_object):
    members = [(e, getattr(sc_object, e)) for e in dir(sc_object)]
    return [(k,v) for k,v in members if type(v).__name__=='CPPOverload']
     
def get_ports(module):
    res = []
    for elem in dir(module):
        attr=getattr(module, elem)
        if isinstance(attr, cppyy.gbl.sc_core.sc_port_base)  and not isinstance(attr, cppyy.gbl.tlm.tlm_base_socket_if):
            res.append(attr)
    return res

def get_exports(module):
    res = []
    for elem in dir(module):
        attr=getattr(module, elem)
        if isinstance(attr, cppyy.gbl.sc_core.sc_export_base) and not isinstance(attr, cppyy.gbl.tlm.tlm_base_socket_if):
            res.append(attr)
    return res

def get_inititator_sockets(module):
    res = []
    for elem in dir(module):
        attr=getattr(module, elem)
        if isinstance(attr, cppyy.gbl.sc_core.sc_port_base) and isinstance(attr, cppyy.gbl.tlm.tlm_base_socket_if):
            res.append(attr)
    return res

def get_target_sockets(module):
    res = []
    for elem in dir(module):
        attr=getattr(module, elem)
        if isinstance(attr, cppyy.gbl.sc_core.sc_export_base) and isinstance(attr, cppyy.gbl.tlm.tlm_base_socket_if):
            res.append(attr)
    return res

def get_submodules(module):
    res = []
    for elem in dir(module):
        attr=getattr(module, elem)
        if isinstance(attr, cppyy.gbl.sc_core.sc_module):
            res.append(attr)
    return res

import time

class timewith():
    def __init__(self, name=''):
        self.name = name
        self.start = time.time()

    @property
    def elapsed(self):
        return time.time() - self.start

    def checkpoint(self, name=''):
        return '{timer} {checkpoint} took {elapsed} seconds'.format(timer=self.name, checkpoint=name, elapsed=self.elapsed).strip()

    def __enter__(self):
        return self

    def __exit__(self, mytype, value, traceback):
        print(self.checkpoint('finished'))
        pass

#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

import json
import cppyy
import os.path
from pathlib import Path
from sysconfig import get_paths
import sys
import re
import tempfile
import conans.client.conan_api as conan
from contextlib import (redirect_stdout, redirect_stderr)
import io

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
        
        
def read_config_from_conan(conanfile, build_type='Release'):
    global lang_level
    sys.stdout = NullLogger()
    #read conan configuration
    with tempfile.TemporaryDirectory() as tmpdirname:
        conan_api, client_cache, user_io = conan.Conan.factory() 
        install_info = conan_api.install(path=conanfile, 
                                         generators=['json'],
                                         settings=['build_type=%s'%build_type],
                                         install_folder=tmpdirname)
    
        for e in install_info['installed']:
            name = e['recipe']['name']
            for p in e['packages']:
                if name == 'SystemC' and p['cpp_info']['rootpath']:
                    os.environ['SYSTEMC_HOME']=p['cpp_info']['rootpath']
                elif name == 'SystemC-CCI' and p['cpp_info']['rootpath']:
                    os.environ['CCI_HOME']=p['cpp_info']['rootpath']
                elif name == 'SystemCVerification' and p['cpp_info']['rootpath']:
                    os.environ['SCV_HOME']=p['cpp_info']['rootpath']
        with open(os.path.join(tmpdirname, "conanbuildinfo.json")) as f:
            data=json.load(f)   
    # set include pathes and load libraries
    for d in data['dependencies']:
        for p in d['include_paths']:
            add_sys_include_path(p)
        if d['name'] == 'SystemC':
            for l in d['lib_paths']:
                if os.path.exists(l+'/'+'libsystemc.so'):
                    cppyy.load_library(l+'/'+'libsystemc.so')
    lang_level = int(data['options']['SystemC']['stdcxx'])
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
    if 'CCI_HOME' in os.environ:
        add_sys_include_path(os.path.join(os.environ['CCI_HOME'], 'include'))
        for l in ['lib', 'lib64', 'lib-linux', 'lib-linux64']:
            for f in ['libcciapi.so']:
                full_file = os.path.join(os.environ['CCI_HOME'], l, f)
                if os.path.isfile(full_file):
                    cppyy.load_library(full_file)
        cppyy.include("cci_configuration")
        cci_loaded=True
        return True
    return False

def _load_pythonization_lib():
    info = get_paths()
    for file in os.listdir(info['platlib']):
        if re.match(r'pysyscsc.*\.so', file):
            cppyy.load_library(os.path.join(info['platlib'], file))
            full_path = os.path.join(info['data'], 'include/site/python%d.%d/PySysC/PyScModule.h' % sys.version_info[:2])
            if os.path.isfile(full_path):
                cppyy.include(full_path)
            return


def add_library(file, lib):
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        cppyy.load_library(lib)
        cppyy.include(file)
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

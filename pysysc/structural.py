#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

from cppyy import gbl as cpp
from builtins import getattr
import re
from enum import Enum

class Mode(Enum):
    SIM = 1
    BUILD = 2

mode=Mode.SIM

module_list = list()
connection_list = list()

def dump_structure():
    mports=dict()
    
    def add_port(p, io):
        mod = p.get_parent_object()
        if mod not in mports:
            mports[mod]=dict()
            mports[mod]['in']=[]
            mports[mod]['out']=[]
        if not p in mports[mod][io]:
            mports[mod][io].append(p)
        
    for c in connection_list:
        add_port(c.source, 'out')
        for t in c.targets:
            add_port(t, 'in')
        
    with open("structure.dot", "w") as f:
        f.write("""digraph structs {
    rankdir=LR
    node [shape=record];\n""")
        for m in mports.keys():
            #struct3 [shape=record,label="hello\nworld |{ b |{c|<here> d|e}| f}| g | h"];
            in_names=['<%s> %s'%(p.basename(), p.basename()) for p in mports[m]['in']]
            out_names=['<%s> %s'%(p.basename(), p.basename()) for p in mports[m]['out']]
            if len(in_names) == 0:
                f.write('  %s [shape=record,label="{%s|{%s}}"];\n' % (
                    m.name(), m.basename(), '|'.join(out_names)))
            elif len(out_names) == 0:
                f.write('  %s [shape=record,label="{{%s}|%s}"];\n' % (
                    m.name(), '|'.join(in_names), m.basename()))
            else:
                f.write('  %s [shape=record,label="{{%s}|%s|{%s}}"];\n' % (
                    m.name(), '|'.join(in_names), m.basename(), '|'.join(out_names)))
        for c in connection_list:
            attr = 'dir=both arrowhead=box arrowtail=obox'
            if isinstance(c, Signal):
                attr = 'dir=none'
            src = '%s:%s' % (c.source.get_parent_object().name(), c.source.basename())
            for t in c.targets:
                tgt = '%s:%s' % (t.get_parent_object().name(), t.basename())
                f.write("    %s -> %s [%s];\n" % (src, tgt, attr))
        f.write("}\n")
        
class Simulation(object):
    
    @staticmethod
    def run():
        cpp.sc_core.sc_start()
        if not cpp.sc_core.sc_end_of_simulation_invoked():
            cpp.sc_core.sc_stop()
        
            
    def __init__(self):
        pass
    
class Module(object):
    '''
    classdocs
    '''
    def __init__(self, clazz):
        self.cppclazz=clazz
        self.instance=None
        module_list.append(self)
    
    def __getattr__(self, attr):
        if self.instance is None:
            raise AttributeError
        return getattr(self.instance, attr)
    
    def create(self, name, *args):
        sc_name = cpp.sc_core.sc_module_name(str(name))
        if args:
            self.instance = self.cppclazz(sc_name, *args)
        else:
            self.instance = self.cppclazz(sc_name)
        return self

class Connection(object):
    '''
    classdocs
    '''
    def __init__(self):
        self.source=None
        self.targets=[]
        connection_list.append(self)
    
    def src(self, module_port):
        self.source=module_port
        return self
    
    def sink(self, module_port):
        self.targets.append(module_port)
        #TODO: add try block and print types of both ports in case of a missmatch
        self.source.bind(module_port)
        return self

    def cross(self, module_port_in, module_port_out):
        self.targets.append(module_port_in)
        self.source.bind(module_port_in)
        return Connection().src(module_port_out)
        
class Signal(Connection):
    '''
    classdocs
    '''

    _sc_inout_re = re.compile(r'^sc_core::sc_(?:_in)?out<(.*)>$')
    _sc_in_re = re.compile(r'^sc_core::sc_in<(.*)>$')
    _sc_port_re = re.compile(r'^sc_core::sc_port<[^<]*<(.*)> ?>$')

    def __init__(self, name=None):
        Connection.__init__(self)
        self.name=name
        self.signal=None
        self.data_type=None
        
    def create_signal(self, module_port):
        if self.signal is None:
            port_class_name = type(module_port).__cpp_name__
            match = self._sc_inout_re.match(port_class_name)
            if match:
                self.data_type = match.group(1)
            else:
                match = self._sc_in_re.match(port_class_name)
                if match:
                    self.data_type = match.group(1)
                else:
                    match = self._sc_port_re.match(port_class_name)
                    if match:
                        self.data_type = match.group(1)
            if self.data_type is None:
                raise AttributeError
            py_dt_name = self.data_type.replace("::", ".").replace("<", "[").replace(">", "]")
            self.signal = eval("cpp.sc_core.sc_signal[cpp.%s](self.name)" % py_dt_name)
            
    def src(self, module_port):
        self.source=module_port
        self.create_signal(module_port)
        module_port.bind(self.signal)
        return self
    
    def sink(self, module_port):
        self.targets.append(module_port)
        self.create_signal(module_port)
        module_port.bind(self.signal)
        return self
        
    def cross(self, module_port_in, module_port_out):
        self.targets.append(module_port_in)
        self.source.bind(module_port_in)
        return Signal().src(module_port_out)

class SignalVector(Connection):
    '''
    classdocs
    '''

    _sc_inout_re = re.compile(r'^sc_core::sc_vector<sc_core::sc_(?:_in)?out<(.*)> ?>$')
    _sc_in_re = re.compile(r'^sc_core::sc_vector<sc_core::sc_in<(.*)> ?>$')
    _sc_port_re = re.compile(r'^sc_core::sc_vector<sc_core::sc_port<[^<]*<(.*)> ?> ?>$')

    def __init__(self, name=None):
        Connection.__init__(self)
        self.name=name
        self.signal=None
        self.data_type=None
        
    def create_signal(self, module_port):
        if self.signal is None:
            port_class_name = type(module_port).__cpp_name__
            match = self._sc_inout_re.match(port_class_name)
            if match:
                self.data_type = match.group(1)
            else:
                match = self._sc_in_re.match(port_class_name)
                if match:
                    self.data_type = match.group(1)
                else:
                    match = self._sc_port_re.match(port_class_name)
                    if match:
                        self.data_type = match.group(1)
            if self.data_type is None:
                raise AttributeError
            py_dt_name = self.data_type.replace("::", ".").replace("<", "[").replace(">", "]")
            self.signal = eval("cpp.sc_core.sc_signal[cpp.%s](self.name)" % py_dt_name)
            
    def src(self, module_port):
        self.source=module_port
        self.create_signal(module_port)
        module_port.bind(self.signal)
        return self
    
    def sink(self, module_port):
        self.targets.append(module_port)
        self.create_signal(module_port)
        module_port.bind(self.signal)
        return self

class Clock(Connection):
    '''
    classdocs
    '''
    _sc_time_re = re.compile(r'^sc_core::sc_in<sc_core::sc_time>')

    def __init__(
            self, 
            name=None, 
            period=1.0, 
            time_unit='SC_NS', 
            duty_cycle=0.5, 
            start_time=0, 
            posedge_first=True):
        Connection.__init__(self)
        self.name=name
        self.clk_tgl = cpp.sc_core.sc_clock(
            'sc_clock_'+self.name, 
            cpp.sc_core.sc_time(period, eval(f"cpp.sc_core.{time_unit}")),
            duty_cycle, 
            cpp.sc_core.sc_time(start_time, eval(f"cpp.sc_core.{time_unit}")), 
            posedge_first)
        self.clk_time = None
        
    def sink(self, module_port):
        self.targets.append(module_port)
        port_class_name = type(module_port).__cpp_name__
        match = self._sc_time_re.match(port_class_name)
        if match:
            if self.clk_time is None:
                self.clk_time = cpp.sc_core.sc_signal[cpp.sc_core.sc_time](self.name)
                self.clk_time.write(self.clk_tgl.period())
            module_port.bind(self.clk_time)
        else:
            module_port.bind(self.clk_tgl)
        
        return self


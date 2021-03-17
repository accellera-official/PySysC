#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

from cppyy import gbl as cpp
from builtins import getattr
import re
from enum import Enum
import logging

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
        
    @staticmethod
    def setup(log_level = logging.WARNING):
        try:
            if log_level >= logging.FATAL:
                cpp.scc.init_logging(cpp.logging.FATAL, False)
            elif log_level >= logging.ERROR:
                cpp.scc.init_logging(cpp.logging.ERROR, False)
            elif log_level >= logging.WARNING:
                cpp.scc.init_logging(cpp.logging.WARNING, False)
            elif log_level >= logging.INFO:
                cpp.scc.init_logging(cpp.logging.INFO, False)
            elif log_level >= logging.DEBUG:
                cpp.scc.init_logging(cpp.logging.DEBUG, False)
            else:
                cpp.scc.init_logging(cpp.logging.TRACE, False)
        except Exception: # fall back: use basic SystemC logging setup
            verb_lut={
                logging.FATAL:100, #SC_LOW
                logging.ERROR: 200, #SC_MEDIUM
                logging.WARNING: 300, #SC_HIGH
                logging.INFO: 400, #SC_FULL
                logging.DEBUG: 500 #SC_DEBUG
                }
            cpp.sc_core.sc_report_handler.set_verbosity_level(verb_lut[log_level]);
        cpp.sc_core.sc_report_handler.set_actions(cpp.sc_core.SC_ID_MORE_THAN_ONE_SIGNAL_DRIVER_, cpp.sc_core.SC_DO_NOTHING);
        #try:
        #    cpp.scc.init_cci("GlobalBroker")
        #except Exception:
        #    pass

    @staticmethod
    def configure(name="", enable_vcd=False):
        if len(name) and os.path.isfile(name):
            Simulation.cfg = cpp.scc.configurer(cpp.std.string(name));
            if enable_vcd:
                trace_name = os.path.basename(name)
                Simulation.trace = cpp.scc.configurable_tracer(trace_name, 1, True, True)
                Simulation.trace.add_control()        
        else:
            if enable_vcd:
                Simulation.trace = cpp.scc.tracer('vcd_trace', 1, True)
            
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
    
    def create(self, name):
        self.instance = self.cppclazz(cpp.sc_core.sc_module_name(str(name)))
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
    _sc_port_re = re.compile(r'^sc_core::sc_port<[^<]*<(.*)>>$')


    def __init__(self, name=None):
        Connection.__init__(self)
        self.name=name
        self.signal=None
        self.data_type=None
        
    def src(self, module_port):
        self.source=module_port
        port_class_name=type(module_port).__cpp_name__
        match = self._sc_inout_re.match(port_class_name)
        if match:
            self.data_type=match.group(1)
        else:
            match = self._sc_port_re.match(port_class_name)
            if match:
                self.data_type=match.group(1)
        if self.data_type is None:
            raise AttributeError;
        py_dt_name=self.data_type.replace("::", ".").replace("<", "[").replace(">", "]")
        self.signal = eval("cpp.sc_core.sc_signal[cpp.%s](self.name)" % py_dt_name)
        module_port.bind(self.signal)
        return self
    
    def sink(self, module_port):
        self.targets.append(module_port)
        module_port.bind(self.signal)
        return self
        
    def cross(self, module_port_in, module_port_out):
        self.targets.append(module_port_in)
        self.source.bind(module_port_in)
        return Signal().src(module_port_out)

#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

import json
import cppyy
import os.path
import pysysc as scpy
from cppyy import gbl as cpp

proj_home='../../PySysC-SC'
conan_res = scpy.read_config_from_conan(os.path.join(proj_home, 'conanfile.txt'))
scpy.load_systemc()
scpy.add_include_path(os.path.join(proj_home, 'sc-components/incl'))
scpy.add_library('scc.h', os.path.join(proj_home, 'build/Debug/lib/libscc.so'))
scpy.add_include_path(os.path.join(proj_home, 'components'))
scpy.add_library('components.h', os.path.join(proj_home, 'build/Debug/lib/libcomponents.so'))

initiator = cpp.Initiator(cpp.sc_core.sc_module_name("initiator"))
memories = [cpp.Memory(cpp.sc_core.sc_module_name(name)) for name in ["mem0", "mem1", "mem2", "mem3"]]
router = cpp.Router[4](cpp.sc_core.sc_module_name("router"))

members = scpy.get_members(initiator)
methods = scpy.get_methods(initiator)

ports =  scpy.get_ports(initiator)
intors = scpy.get_inititator_sockets(initiator)
tgts =   scpy.get_target_sockets(initiator)
childs = scpy.get_submodules(initiator)

cppyy.cppdef("""
class my_module: public sc_core::sc_module {
public:
    sc_core::sc_out<sc_dt::sc_uint<32>> port;
    my_module(sc_core::sc_module_name nm):sc_core::sc_module(nm), port("port"){}
};
void bind_port(sc_core::sc_signal<sc_dt::sc_uint<32>>& s, sc_core::sc_out<sc_dt::sc_uint<32>>& p){p(s);}
""")

class MyMod(cpp.sc_core.sc_module):
    def __init__(self, name):
        cpp.sc_core.sc_module.sc_module()
    
mod = cpp.my_module(cpp.sc_core.sc_module_name("module"))
sig = cpp.sc_core.sc_signal[cpp.sc_dt.sc_uint[32]]("signal")
mod.port(sig)

mod2 = MyMod("Blah")

initiator.socket.bind(router.target_socket)
for idx,m in enumerate(memories):
    router.initiator_socket.at(idx).bind(m.socket)
time = cpp.sc_core.sc_time_stamp()
print(intors[0].name(), "connects to sc_object:", isinstance(intors[0][0], cpp.sc_core.sc_object))
cpp.sc_core.sc_in_action=True
cpp.sc_core.sc_start()
print("Done at", cpp.sc_core.sc_time_stamp())

#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

import cppyy
cppyy.add_include_path('.')
cppyy.load_library('../lib/libsystemc.so.2.3.3')
cppyy.include('cppyy_systemc.h')
cppyy.include('sysc/kernel/sc_module.h')
import pdb

from cppyy.gbl import sc_core
from pprint import pprint as pp

#pprint(dir(cppyy.gbl.sc_dt))
cppyy.cppdef("""
class my_module: public sc_core::sc_module {
public:
	sc_core::sc_signal<sc_dt::sc_uint<32>> sig;
	sc_core::sc_out<sc_dt::sc_uint<32>> port;
	my_module():sc_core::sc_module("module"), sig("sig"){}
};
void bind_port(sc_core::sc_signal<sc_dt::sc_uint<32>>& s, sc_core::sc_out<sc_dt::sc_uint<32>>& p){p(s);}
""")
v=cppyy.gbl.std.vector[int](10)
#n = sc_module()
n = cppyy.gbl.my_module()
pp(sc_core.sc_time_stamp().to_string())
pp(n.simcontext().time_stamp().to_string())
print(type(n.port).__name__ +", "+type(n.port).__cpp_name__)
print(type(n.sig).__name__+", "+type(n.sig).__cpp_name__)

#try:
#	cppyy.cppdef("""blah /* a comment */""");
#except:
#	print("No success")

pdb.set_trace()

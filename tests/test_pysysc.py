#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

import unittest
import json
import cppyy
import os.path
import pysysc as scpy
from cppyy import gbl as cpp


class Test(unittest.TestCase):

    not_initialized=True

    def setUp(self):
        if  Test.not_initialized:
            proj_home='../../PySysC-SC'
            conan_path=os.path.join(proj_home, 'conanfile.txt')
            conan_res = scpy.read_config_from_conan(conan_path)
            scpy.load_systemc()
            scpy.add_include_path(os.path.join(proj_home, 'sc-components/incl'))
            scpy.add_library('scc.h', os.path.join(proj_home, 'build/Debug/lib/libscc.so'))
            scpy.add_include_path(os.path.join(proj_home, 'components'))
            scpy.add_library('components.h', os.path.join(proj_home, 'build/Debug/lib/libcomponents.so'))
            
            
            ###############################################################################
            # instantiate
            ###############################################################################
            Test.clkgen = cpp.ClkGen(cpp.sc_core.sc_module_name("clk_gen"))
            Test.rstgen = cpp.ResetGen(cpp.sc_core.sc_module_name("rst_gen"))
            Test.initiator = cpp.Initiator(cpp.sc_core.sc_module_name("initiator"))
            Test.memories = [cpp.Memory(cpp.sc_core.sc_module_name(name)) for name in ["mem0", "mem1", "mem2", "mem3"]]
            Test.router = cpp.Router[4](cpp.sc_core.sc_module_name("router"))
            ###############################################################################
            # signals
            ###############################################################################
            Test.sig_clk = cpp.sc_core.sc_signal[cpp.sc_core.sc_time]("clk")
            Test.sig_rst = cpp.sc_core.sc_signal[cpp.sc_dt.sc_logic]("rst")
            ###############################################################################
            # connect it
            ###############################################################################
            Test.clkgen.clk_o(Test.sig_clk)
            Test.rstgen.reset_o(Test.sig_rst)
            Test.initiator.socket.bind(Test.router.target_socket)
            Test.initiator.clk_i(Test.sig_clk)
            Test.initiator.reset_i(Test.sig_rst)
            Test.router.clk_i(Test.sig_clk)
            Test.router.reset_i(Test.sig_rst)
            for idx,m in enumerate(Test.memories):
                Test.router.initiator_socket.at(idx).bind(m.socket)
                m.clk_i(Test.sig_clk)
                m.reset_i(Test.sig_rst)

            Test.not_initialized=False

    def tearDown(self):
        #cpp.sc_core.sc_stop()
        pass


    def testSCTimeRepr(self):
        cur_time=cpp.sc_core.sc_time_stamp()
        cur_time_str=cur_time.to_string()
        self.assertEqual(cur_time_str, '0 s')

    def testMembers(self):
        members = scpy.get_members(Test.initiator)
        print("members")
        methods = scpy.get_methods(Test.initiator)
        print("methods")
        ports =  scpy.get_ports(Test.initiator)
        print("ports")
        intors = scpy.get_inititator_sockets(Test.initiator)
        print("intors")
        tgts =   scpy.get_target_sockets(Test.initiator)
        print("tgts")
        childs = scpy.get_submodules(Test.initiator)
        print("childs")
        self.assertTrue(len(intors)==1, "Wrong numbers of initiator sockets")
        
    def testConnection(self):
        intors = scpy.get_inititator_sockets(Test.initiator)
        self.assertFalse(isinstance(intors[0][0], cpp.sc_core.sc_object), " intor[0] connects to sc_object", )

#    def testSim(self):
#        cpp.sc_core.sc_in_action=True
#        cpp.sc_core.sc_start()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

import os.path
import logging
import cppyy
from cppyy import gbl as cpp
import pysysc
from pysysc.structural import Connection, Module, Signal, Simulation

num_of_mem = 100

class TopModule(cpp.scc.PyScModule):
    
    def __init__(self, name):
        super().__init__(self, name)
        ###############################################################################
        # instantiate
        ###############################################################################
        self.clk_gen = Module(cpp.ClkGen).create("clk_gen")
        self.rst_gen = Module(cpp.ResetGen).create("rst_gen")
        self.initiator = Module(cpp.Initiator).create("initiator")
        self.memories = [Module(cpp.Memory).create("mem%d"%idx) for idx in range(0,num_of_mem)]
        self.router = Module(cpp.Router[num_of_mem]).create("router")
        ###############################################################################
        # connect them
        ###############################################################################
        self.clk = Signal("clk").src(self.clk_gen.clk_o).sink(self.initiator.clk_i).sink(self.router.clk_i)
        [self.clk.sink(m.clk_i) for m in self.memories]
        self.rst = Signal("rst").src(self.rst_gen.reset_o).sink(self.initiator.reset_i).sink(self.router.reset_i)
        [self.rst.sink(m.reset_i) for m in self.memories]
        Connection().src(self.initiator.socket).sink(self.router.target_socket)
        [Connection().src(self.router.initiator_socket.at(idx)).sink(m.socket) for idx,m in enumerate(self.memories)]
        super().method("TickMethod", [self.clk.signal.pos_edge()])
        
        
    def EndOfElaboration(self):
        print("Elaboration finished")
        
    def StartOfSimulation(self):
        print("Simulation started")
        
    def EndOfSimulation(self):
        print("Simulation finished")
        
    def TickMethod(self):
        print("Simulation tick")

###############################################################################
# setup  and load
###############################################################################
logging.basicConfig(level=logging.INFO)
build_type='Debug'
###############################################################################
#myDir = os.path.dirname( os.path.realpath(__file__))
myDir = os.path.dirname( os.path.realpath(__file__)+'/../../PySysC-SC')
pysysc.read_config_from_conan(os.path.join(myDir, 'conanfile.txt'), build_type)
pysysc.load_systemc()
###############################################################################
logging.debug("Loading SC-Components lib")
pysysc.add_include_path(os.path.join(myDir, 'sc-components/incl'))
pysysc.add_library('scc.h', os.path.join(myDir, 'build/%s/lib/libsc-components.so'%build_type))
###############################################################################
logging.debug("Loading Components lib")
pysysc.add_include_path(os.path.join(myDir, 'components'))
pysysc.add_library('components.h', os.path.join(myDir, 'build/%s/lib/libcomponents.so'%build_type))
###############################################################################
# configure
###############################################################################
Simulation.setup(logging.root.level)
###############################################################################
# instantiate
###############################################################################
#from modules import TopModule
dut = Module(TopModule).create("dut")
###############################################################################
# run if it is standalone
###############################################################################
if __name__ == "__main__":
    Simulation.configure(enable_vcd=False)
    Simulation.run()
    logging.debug("Done")

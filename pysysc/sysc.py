#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

'''
Created on 30.08.2021

@author: eyck
'''
from cppyy import gbl as cpp

class ScModule(cpp.scc.PyScModule):
    '''
    classdocs
    '''
    
    def __init__(self, name):
        super().__init__(self, name)
    
    def __getattr__(self, attr):
        if self.instance is None:
            raise AttributeError
        return getattr(self.instance, attr)
    
    def ScMethod(self, func, sensitivity=[], initialize=False):
        pass


/*
 * Copyright (c) 2019 -2021 MINRES Technolgies GmbH
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "PyScModule.h"
#define PY_SSIZE_T_CLEAN
#include <python3.6/Python.h>

class TPyScriptThreadLocker {
    PyGILState_STATE m_state;
public:
    TPyScriptThreadLocker(): m_state(PyGILState_Ensure()) {}
    ~TPyScriptThreadLocker() { PyGILState_Release(m_state); }
};

scc::PyScModule::PyScModule(PyObject*  self, const sc_core::sc_module_name& nm)
: sc_core::sc_module(nm)
, self(self)
{
    if (! PyEval_ThreadsInitialized())
        PyEval_InitThreads();
    Py_INCREF(self);
}

scc::PyScModule::~PyScModule() {
    Py_DECREF(self);
}

void scc::PyScModule::before_end_of_elaboration(){
    invoke_callback("BeforeEndOfElaboration");
}

void scc::PyScModule::end_of_elaboration(){
    invoke_callback("EndOfElaboration");
}
void scc::PyScModule::start_of_simulation(){
    invoke_callback("StartOfSimulation");
}

void scc::PyScModule::end_of_simulation(){
    invoke_callback("EndOfSimulation");
}

void scc::PyScModule::invoke_callback(const char* callback_name) {
    // acquiring the GIL
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();
    if(PyObject_HasAttrString(self, callback_name)){
        auto* func = PyObject_GetAttrString(self, callback_name);
        PyObject_CallFunctionObjArgs(func, nullptr);
    }
    // Release the thread. No Python API allowed beyond this point.
    PyGILState_Release(gstate);
}

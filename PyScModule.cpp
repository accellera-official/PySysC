/*
 * Copyright (c) 2019 -2021 MINRES Technolgies GmbH
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#define SC_INCLUDE_DYNAMIC_PROCESSES
#include "PyScModule.h"
#define PY_SSIZE_T_CLEAN
#include <Python.h>

class TPyScriptThreadLocker {
    PyGILState_STATE m_state;
public:
    TPyScriptThreadLocker(): m_state(PyGILState_Ensure()) {}
    ~TPyScriptThreadLocker() { PyGILState_Release(m_state); }
};

scc::PyScModule::PyScModule(PyObject* self, const sc_core::sc_module_name& nm)
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

void scc::PyScModule::ScThread(std::string fname) {
    sc_core::sc_spawn_options opts;
    auto run_handle = sc_core::sc_spawn([this, fname](){
        invoke_callback(fname);
    }, nullptr, &opts);
    this->sensitive << run_handle;
    this->sensitive_pos << run_handle;
    this->sensitive_neg << run_handle;
}
void scc::PyScModule::invoke_callback(std::string const& callback_name) {
   if(PyObject_HasAttrString(self, callback_name.c_str())){
        // acquiring the GIL
        gstate = PyGILState_Ensure();
        auto* func = PyObject_GetAttrString(self, callback_name.c_str());
        PyObject_CallFunctionObjArgs(func, nullptr);
        // Release the thread. No Python API allowed beyond this point.
        PyGILState_Release(gstate);
    }
}

void scc::PyScModule::ScWait() {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait();
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(const sc_core::sc_event& e){
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(e);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(const sc_core::sc_event_or_list &el) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(el);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(const sc_core::sc_event_and_list &el) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(el);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(const sc_core::sc_time &t) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(t);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(double v, sc_core::sc_time_unit tu) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(v, tu);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(const sc_core::sc_time &t, const sc_core::sc_event &e) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(t, e);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(double v, sc_core::sc_time_unit tu, const sc_core::sc_event &e) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(v, tu, e);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(const sc_core::sc_time &t, const sc_core::sc_event_or_list &el) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(t, el);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(double v, sc_core::sc_time_unit tu, const sc_core::sc_event_or_list &el) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(v, tu, el);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(const sc_core::sc_time &t, const sc_core::sc_event_and_list &el) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(t, el);
    gstate = PyGILState_Ensure();
}

void scc::PyScModule::ScWait(double v, sc_core::sc_time_unit tu, const sc_core::sc_event_and_list &el) {
    PyGILState_Release(gstate);
    sc_core::sc_module::wait(v, tu, el);
    gstate = PyGILState_Ensure();
}

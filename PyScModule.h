/*
 * Copyright (c) 2019 -2021 MINRES Technolgies GmbH
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef COMPONENTS_PYSCMODULE_H_
#define COMPONENTS_PYSCMODULE_H_
#include <systemc>
#include <unordered_map>
#include <tuple>
#define PY_SSIZE_T_CLEAN
#include <Python.h>


typedef struct _object  PyObject;

namespace scc {

class PyScModule: public sc_core::sc_module {
public:
    PyScModule(PyObject*  self, const sc_core::sc_module_name& nm);
    virtual ~PyScModule();

    void ScThread(std::string fname);
    void ScWait();
    void ScWait( const sc_core::sc_event& e );
    void ScWait( const sc_core::sc_event_or_list& el );
    void ScWait( const sc_core::sc_event_and_list& el );
    void ScWait( const sc_core::sc_time& t );
    void ScWait( double v, sc_core::sc_time_unit tu );
    void ScWait( const sc_core::sc_time& t,          const sc_core::sc_event& e );
    void ScWait( double v, sc_core::sc_time_unit tu, const sc_core::sc_event& e );
    void ScWait( const sc_core::sc_time& t,          const sc_core::sc_event_or_list& el );
    void ScWait( double v, sc_core::sc_time_unit tu, const sc_core::sc_event_or_list& el );
    void ScWait( const sc_core::sc_time& t,          const sc_core::sc_event_and_list& el );
    void ScWait( double v, sc_core::sc_time_unit tu, const sc_core::sc_event_and_list& el );

protected:
    void before_end_of_elaboration() override;
    void end_of_elaboration() override;
    void start_of_simulation() override;
    void end_of_simulation() override;
private:
    void invoke_callback(std::string const&);
    PyObject* self{nullptr};
    PyGILState_STATE gstate;
};

}
#endif /* COMPONENTS_PYSCMODULE_H_ */

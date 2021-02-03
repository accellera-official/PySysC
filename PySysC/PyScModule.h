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

typedef struct _object  PyObject;

namespace scc {

class PyScModule: public sc_core::sc_module {
public:
    PyScModule(PyObject*  self, const sc_core::sc_module_name& nm);
    virtual ~PyScModule();
protected:
    void before_end_of_elaboration() override;
    void end_of_elaboration() override;
    void start_of_simulation() override;
    void end_of_simulation() override;
private:
    void invoke_callback(const char*);
    PyObject* self{nullptr};
};

}
#endif /* COMPONENTS_PYSCMODULE_H_ */

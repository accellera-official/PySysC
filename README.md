# PySysC

A Python 3 package to use SystemC from Python

## How to setup the environment

The installation for PySysC is as follows (using bash shell):

```
# create virtual environment
python3 -m venv pysysc-env
# and enable it
. pysysc-env/bin/activate
# install needed packages
python3 -m pip install wheel
# install cppyy, C++ std version needs to match the version used to build the SystemC library
STDCXX=11 python3 -m pip install cppyy
# clone of PySysC
git clone https://git.minres.com/SystemC/PySysC.git
# install PySysC, for development PySysC use 'python3 -m pip install -e`
python3 -m pip install -e PySysC
```

## Testing (preliminary)

To use the tests you also need to clone and build the PySysC-SC repo as sibling of PySysC. It contains the the code and libraries being used in the test.

## TODO

* pythonize `sc_module` with iteration protocol (`__next__` and `StopIteration`  exception)

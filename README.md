# PySysC

A Python package to make SystemC usable from Python

## How to setup the environment

The installation for PySysC is as follows (using bash shell). The process has
been tested under CentOS7 and Ubuntu 20.04. Make sure a newer version of gcc 
is in your path (tested with gcc-6.3.0). Also the SystemC installation has to
be reference with the environment variable SYSTEMC_HOME.

If you get an error complaining about 
missing Python.h, you need to install Python development headers. See the 
articel under https://blog.ducthinh.net/gcc-no-such-file-python-h.

```
# create virtual environment
python3 -m venv pysysc-env
# and avtivate it
. pysysc-env/bin/activate
# update pip to mekae sure we have the newest version
python3 -m pip install --upgrade pip
# install wheel package
python3 -m pip install wheel
# install cppyy, C++ std version needs to match the version used when building the SystemC library
STDCXX=11 python3 -m pip install cppyy
# clone of PySysC
git clone https://git.minres.com/SystemC/PySysC.git
# install PySysC, for development PySysC use 'python3 -m pip install -e`
SYSTEMC_HOME=<path to SystemC> python3 -m pip install -e PySysC
```

## Running the example

To run the example you need to clone and build the PySysC-SC repo. It contains the the code and libraries being used in the example. This project uses [Conan.io](https://conan.io/) as package manager so it should be installed (see down below).
To deactivate conan and use a SystemC installation just comment out the line `setup_conan()` in CMakeLists.txt and set the environment variable SYSTEMC_HOME.

### Run the router_eample.py

```
# get the PySysC-SC repo
git clone --recursive https://git.minres.com/SystemC/PySysC-SC.git
# build the project libraries as shared libs
cd PySysC-SC
mkdir -p build/Debug
cd build/Debug
cmake -DCMAKE_BUILD_TYPE=Debug -DBUILD_SHARED_LIBS=ON ../..
make -j components
cd ../..
# now we are ready to run the example
python3 router_eample.py

```

### Installing conan separately

conan.io will be installed as part of the PySysC module. To install it seperatly and build the example project without
PySysC you need to execute the following steps:

```
# install conan into our virtual environment pysysc-env
python3 -m pip install conan
# create the default profile
conan profile new default --detect
# add the repo for SystemC packages used in the project
conan remote add minres https://api.bintray.com/conan/minres/conan-repo
```

## TODO

* pythonize `sc_module` with iteration protocol (`__next__` and `StopIteration`  exception)

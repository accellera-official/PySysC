#
# Copyright (c) 2019 -2021 MINRES Technolgies GmbH
#
# SPDX-License-Identifier: Apache-2.0
#

from setuptools import setup, Extension
import os

def readme():
    with open('README.md') as f:
        return f.read()

sysc_home = os.environ['SYSTEMC_HOME']

pysyscsc = Extension('pysyscsc',
                    define_macros = [('MAJOR_VERSION', '1'), ('MINOR_VERSION', '0')],
                    extra_compile_args = ['-std=c++11'],
                    include_dirs = [sysc_home+'/include'],
                    libraries = ['systemc'],
                    library_dirs = [sysc_home+'/lib64', sysc_home+'/lib', sysc_home+'/lib-linux64', sysc_home+'/lib-linux'],
                    sources = ['PyScModule.cpp'],
                    depends = ['PyScModule.h'])


setup(name='PySysC',
    version='0.1',
    description='Python SystemC binding',
    long_description=readme(),
    ext_modules = [pysyscsc],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)'
    ],
    keywords='SystemC simulation',
    url='https://github.com/accellera-official/PySysC',
    author='MINRES Technologies GmbH',
    author_email='info@minres.com',
    license='Apache-2.0',
    packages=['pysysc'],
    package_data={
        'pysyscsc': ['PyScModule.h'],
    },
    #data_files=[('include',['PyScModule.h'])],
    headers=['PyScModule.h'],
    include_package_data=True,
    install_requires=[
        'cppyy',
        'conan'
        ],
    test_suite='nose.collector',
    tests_require=['nose'],
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
from distutils.core import setup

setup(
    name = 'ewave',
    version = '1.0.0',
    py_modules = ['ewave'],
    requires = ['numpy (>=1.0)'],
    
    description = "Extended WAVE I/O",
    long_description = "Pure python module providing support for reading and writing extended WAVE file formats, including IEEE floats.",
    classifiers = ["License :: OSI Approved :: Python Software Foundation License",
                   "Development Status :: 4 - Beta",
                   "Environment :: Console",
                   "Intended Audience :: Developers",
                   "Topic :: Multimedia :: Sound/Audio :: Conversion",
                   "Programming Language :: Python :: 2"],
    
    author = "Dan Meliza",
    maintainer = "Dan Meliza",
    maintainer_email = "dan at meliza.org",
    url = "https://github.com/dmeliza/py-ewave",
    )


# Variables:
# End:

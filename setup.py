#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
from distutils.core import setup

setup(
    name = 'ewave',
    version = '1.0.3',
    py_modules = ['ewave'],
    requires = ['numpy (>=1.0)'],

    description = "Extended WAVE I/O",
    long_description = "Pure python module providing support for reading and writing extended WAVE audio file formats, including IEEE floats and >2 channels.",
    classifiers = ["License :: OSI Approved :: Python Software Foundation License",
                   "Development Status :: 4 - Beta",
                   "Environment :: Console",
                   "Intended Audience :: Developers",
                   "Topic :: Multimedia :: Sound/Audio :: Conversion",
                   "Operating System :: Unix",
                   "Operating System :: POSIX :: Linux",
                   "Operating System :: MacOS :: MacOS X",
                   "Natural Language :: English",
                   "Programming Language :: Python :: 2"],

    author = 'C Daniel Meliza',
    author_email = '"dan" at the domain "meliza.org"',
    maintainer = 'C Daniel Meliza',
    maintainer_email = '"dan" at the domain "meliza.org"',
    url = "https://github.com/dmeliza/py-ewave",
    download_url = "https://github.com/dmeliza/py-ewave/downloads"
    )


# Variables:
# End:

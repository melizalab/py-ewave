#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
from distutils.core import setup

long_desc = """Pure python module providing support for reading and
writing extended WAVE audio file formats, including IEEE floats and >2 channels.
"""

setup(
    name='ewave',
    version='1.1.0-SNAPSHOT',
    py_modules=['ewave'],
    requires=['numpy (>=1.0)'],

    description="Extended WAVE I/O",
    long_description="",
    classifiers=[
        "License :: OSI Approved :: Python Software Foundation License",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Operating System :: Unix",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],

    author='C Daniel Meliza',
    author_email='"dan" at the domain "meliza.org"',
    maintainer='C Daniel Meliza',
    maintainer_email='"dan" at the domain "meliza.org"',
    url="https://github.com/melizalab/py-ewave",
    download_url="https://github.com/melizalab/py-ewave/downloads"
)


# Variables:
# End:

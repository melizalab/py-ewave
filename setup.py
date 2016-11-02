#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import sys
if sys.hexversion < 0x02060000:
    raise RuntimeError("Python 2.6 or higher required")

# setuptools 0.7+ doesn't play nice with distribute, so try to use existing
# package if possible
try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

long_desc = """Pure python module providing support for reading and
writing extended WAVE audio file formats, including IEEE floats and >2 channels.
"""

setup(
    name='ewave',
    version='1.0.5',
    py_modules=['ewave'],

    description="Extended WAVE I/O",
    long_description=long_desc,
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
    author_email='dan@meliza.org',
    maintainer='C Daniel Meliza',
    maintainer_email='dan@meliza.org',
    url="https://github.com/melizalab/py-ewave",
    download_url="https://github.com/melizalab/py-ewave/downloads",

    test_suite='nose.collector'
)


# Variables:
# End:

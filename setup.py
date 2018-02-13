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

from ewave import __version__

cls_txt = """
License :: OSI Approved :: Python Software Foundation License
Development Status :: 5 - Production/Stable
Environment :: Console
Intended Audience :: Developers
Topic :: Multimedia :: Sound/Audio :: Conversion
Operating System :: Unix
Operating System :: POSIX :: Linux
Operating System :: MacOS :: MacOS X
Natural Language :: English
Programming Language :: Python
"""

long_desc = """Pure python module providing support for reading and
writing extended WAVE audio file formats, including IEEE floats and >2 channels.
"""

setup(
    name='ewave',
    version=__version__,
    py_modules=['ewave'],
    install_requires=["numpy>=1.8"],

    description="Extended WAVE I/O",
    long_description=long_desc,
    classifiers=[x for x in cls_txt.split("\n") if x],
    author='Dan Meliza',
    maintainer='Dan Meliza',
    url="https://github.com/melizalab/py-ewave",

    test_suite='nose.collector'
)


# Variables:
# End:

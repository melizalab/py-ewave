# -*- coding: utf-8 -*-
# -*- mode: python -*-
# Copyright (C) 2012 Dan Meliza <dan@meliza.org>
# Created Tue Aug 14 15:03:19 2012

import os
import glob
from nose.tools import *

import wave

test_dir = "test"
unsupported_dir = "unsupported"

def read_file(fname):
    fp = wave.open(fname,"r")
    assert fp.filename == fname
    assert fp.mode == "r"
    data = fp.read()
    if fp.nchannels == 1:
        assert data.ndim == 1
        assert data.size == fp.nframes
    else:
        assert data.shape[0] == fp.nframes
        assert data.shape[1] == fp.nchannels

@raises(wave.Error)
def read_unsupported(fname):
    read_file(fname)
        
def test01_read():
    for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
        yield read_file, fname

def test02_unsupported():
    for fname in glob.iglob(os.path.join(unsupported_dir, "*.wav")):
        yield read_unsupported, fname
        
# Variables:
# End:

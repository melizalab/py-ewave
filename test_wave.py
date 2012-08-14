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
test_file = os.path.join(test_dir,"test.wav")

def setup():
    if os.path.exists(test_file): os.remove(test_file)

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

def compare_fmt(fname):
    """ test against sndfile-info output """
    pass

def write_file(fname):
    fp1 = wave.open(fname,"r")
    fp2 = wave.open(test_file,"w",
                    sampling_rate=fp1.sampling_rate,
                    dtype=fp1.dtype,
                    nchannels=fp1.nchannels)
    assert fp2.filename == test_file
    assert fp2.sampling_rate == fp1.sampling_rate
    assert fp2.dtype == fp1.dtype
    assert fp2.nchannels == fp1.nchannels
    fp2.write(fp1.read())
    assert fp2.nframes == fp1.nframes
    

@raises(wave.Error)
def read_unsupported(fname):
    read_file(fname)
        
def test01_read():
    for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
        yield read_file, fname

def test02_unsupported():
    for fname in glob.iglob(os.path.join(unsupported_dir, "*.wav")):
        yield read_unsupported, fname

def test03_write():
    for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
        yield write_file, fname
    

# Variables:
# End:

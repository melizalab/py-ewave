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

# defaults for test file
test_file = os.path.join(test_dir,"test.wav")
nchan = 2
Fs = 48000

def compare_arrays(a,b,msg):
    from numpy import all
    a,b = a.squeeze(),b.squeeze()
    assert a.shape==b.shape, "%s: shape %s, expected %s" % (msg, a.shape, b.shape)
    assert all(a==b), "%s: arrays unequal" % msg

def setup():
    if os.path.exists(test_file): os.remove(test_file)

def read_file(fname,memmap="r"):
    fp = wave.open(fname,"r")
    assert fp.filename == fname
    assert fp.mode == "r"
    data = fp.read(memmap=memmap)
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
    with wave.open(test_file,"w", 
                    sampling_rate=fp1.sampling_rate,
                    dtype=fp1.dtype,
                    nchannels=fp1.nchannels) as fp2:
        assert fp2.filename == test_file, fname
        assert fp2.sampling_rate == fp1.sampling_rate, fname
        assert fp2.dtype == fp1.dtype, fname
        assert fp2.nchannels == fp1.nchannels, fname
        fp2.write(fp1.read())
        assert fp2.nframes == fp1.nframes, fname
    os.remove(test_file)
    
def readwrite_file(fname):
    """ test files in r+ mode """
    from numpy import concatenate
    fp1 = wave.open(fname,"r")
    d1 = fp1.read()
    with wave.open(test_file,"w", 
                    sampling_rate=fp1.sampling_rate,
                    dtype=fp1.dtype,
                    nchannels=fp1.nchannels) as fp2:
        fp2.write(d1).flush()

    with wave.open(test_file,"r+") as fp3:
        assert fp3.filename == test_file, fname
        assert fp3.sampling_rate == fp1.sampling_rate, fname
        assert fp3.dtype == fp1.dtype, fname
        assert fp3.nchannels == fp1.nchannels, fname
        assert fp3.nframes == fp1.nframes, fname

        d2 = fp3.read(memmap='r+')
        compare_arrays(d1,d2,fname)

    os.remove(test_file)        

@raises(wave.Error)
def read_unsupported(fname):
    read_file(fname)

# minor semantic checks
@raises(ValueError)        
def test00_mode():
    wave.open(test_file,'a')

def test00_handle():
    fp = open(test_file,'w')
    with wave.open(fp,sampling_rate=Fs,nchannels=nchan) as wfp:
        assert wfp.sampling_rate == Fs
        assert wfp.filename == test_file
    os.remove(test_file)

# behavior checks
def test01_read():
    for mmap in (False,'c','r'):
        for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
            yield read_file, fname, mmap

def test01_unsupported():
    for fname in glob.iglob(os.path.join(unsupported_dir, "*.wav")):
        yield read_unsupported, fname

def test01_write():
    for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
        yield write_file, fname

def test01_readwrite():
    for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
        yield readwrite_file, fname

def test02_modify():
    from numpy.random import randn
    data = randn(10000,nchan)
    with wave.open(test_file,"w+",sampling_rate=Fs,dtype='f',nchannels=nchan) as fp:
        fp.write(data)
        d2 = fp.read(memmap='r+')
        compare_arrays(data,d2,"written data")
        d2 *= 2
        compare_arrays(data*2,d2,"modified data")

    with wave.open(test_file,"r") as fp:
        d2 = fp.read(memmap='r')
        compare_arrays(data*2,d2,"written data")

def test02_append():
    from numpy import random, concatenate
    d1 = random.randn(100,nchan)
    d2 = random.randn(100,nchan)
    with wave.open(test_file,"w+",sampling_rate=Fs,dtype='f',nchannels=nchan) as fp:
        fp.write(d1)
        compare_arrays(d1,fp.read(),"first data")
        fp.write(d2)
        compare_arrays(concatenate(d1,d2),fp.read(),"second data")

# Variables:
# End:

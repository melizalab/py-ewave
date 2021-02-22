# -*- coding: utf-8 -*-
# -*- mode: python -*-
# Copyright (C) 2012 Dan Meliza <dan@meliza.org>
# Created Tue Aug 14 15:03:19 2012

from __future__ import division
from __future__ import unicode_literals
import os
import glob
from nose.tools import *
from numpy.testing import assert_array_almost_equal

import ewave

test_dir = "test"
unsupported_dir = "unsupported"

# defaults for test file
test_file = None
nchan = 2
Fs = 48000

def setup():
    import tempfile
    global temp_dir, test_file
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test.wav")

def teardown():
    import shutil
    shutil.rmtree(temp_dir)

def read_file(fname, memmap="r"):
    fp = ewave.open(fname,"r")
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

def write_file(fname,tgt_type=None):
    fp1 = ewave.open(fname,"r")
    with ewave.open(test_file,"w",
                    sampling_rate=fp1.sampling_rate,
                    dtype=tgt_type or fp1.dtype,
                    nchannels=fp1.nchannels) as fp2:
        assert fp2.filename == test_file, fname
        assert fp2.sampling_rate == fp1.sampling_rate, fname
        assert fp2.nchannels == fp1.nchannels, fname
        if not tgt_type: assert fp2.dtype == fp1.dtype, fname
        fp2.write(fp1.read())
        assert fp2.nframes == fp1.nframes, fname
    os.remove(test_file)

def readwrite_file(fname):
    """ test files in r+ mode """
    fp1 = ewave.open(fname,"r")
    d1 = fp1.read()
    with ewave.open(test_file,"w",
                    sampling_rate=fp1.sampling_rate,
                    dtype=fp1.dtype,
                    nchannels=fp1.nchannels) as fp2:
        fp2.write(d1, scale=False).flush()

    with ewave.open(test_file,"r+") as fp3:
        assert fp3.filename == test_file, fname
        assert fp3.sampling_rate == fp1.sampling_rate, fname
        assert fp3.dtype == fp1.dtype, fname
        assert fp3.nchannels == fp1.nchannels, fname
        assert fp3.nframes == fp1.nframes, fname

        d2 = fp3.read(memmap='r+')
        assert_array_almost_equal(d1,d2)

    os.remove(test_file)

@raises(ewave.Error)
def read_unsupported(fname):
    read_file(fname)

def rescale(src_type, tgt_type):
    from numpy import ones,dtype
    d1 = ones(1000,dtype=src_type)
    if dtype(src_type).kind=='f': d1 *= 0.9
    d2 = ewave.rescale(d1, tgt_type)
    assert d2.dtype == dtype(tgt_type)


# minor semantic checks
@raises(ValueError)
def test00_mode():
    ewave.open(test_file,'a')

def test00_handle():
    fp = open(test_file,'wb')
    with ewave.open(fp,sampling_rate=Fs,nchannels=nchan) as wfp:
        assert wfp.sampling_rate == Fs
        assert wfp.filename == test_file
    os.remove(test_file)

def test00_invalidtype():
    if os.path.exists(test_file): os.remove(test_file)
    try:
        ewave.open(test_file,'w',dtype='S2')
    except ewave.Error:
        # verify that file was not created
        assert not os.path.exists(test_file), "file was created for invalid type"
        return
    raise Exception("Exception was not raised for invalid type")


def test00_intformat():
    """integer types stored as WAVE_FORMAT_PCM"""
    from numpy import zeros
    dtype = "i"
    data = zeros(1000, dtype=dtype)
    fp = open(test_file, "wb")
    with ewave.open(fp, dtype=dtype, sampling_rate=Fs, nchannels=nchan) as wfp:
        wfp.write(data)
    fp.close()
    with ewave.open(test_file, "r") as rfp:
        assert rfp._tag == ewave.WAVE_FORMAT_PCM


def test00_floatformat():
    """float types stored as WAVE_FORMAT_IEEE_FLOAT"""
    from numpy import zeros
    dtype = "f"
    data = zeros(1000, dtype=dtype)
    fp = open(test_file, "wb")
    with ewave.open(fp, dtype=dtype, sampling_rate=Fs, nchannels=nchan) as wfp:
        wfp.write(data)
    fp.close()
    with ewave.open(test_file, "r") as rfp:
        assert rfp._tag == ewave.WAVE_FORMAT_IEEE_FLOAT


@raises(ewave.Error)
def test00_rescalebad():
    ewave.rescale([1,2,3],'S2')


# behavior checks
def test01_rescaletypes():
    dtypes = ('u1','h','i','l','f','d')
    for src in dtypes:
        for tgt in dtypes:
            yield rescale, src, tgt


# tests rescaling at edges
def test01_rescalevalues():
    from numpy import array
    tests = ((32767, 'h', 1 - 1 / (1 << 15)),
             (32768, 'h', -1.0),
             ((1 << 31) - 1, 'i', 1 - 1 / (1 << 31)),
             (1 << 31, 'i', -1.0),)
    for val, dtype, expected in tests:
        assert_almost_equal(ewave.rescale(array([val], dtype), 'f')[0], expected)


def test01_clipping():
    assert_almost_equal(ewave.rescale(ewave.rescale([-1.01], 'h'), 'f')[0], -1.0)
    assert_almost_equal(ewave.rescale(ewave.rescale([1.01], 'i'), 'f')[0], 1.0)


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

def test01_convert():
    for tgt_type in ('f','h'):
        for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
            yield write_file, fname, tgt_type

def test01_readwrite():
    for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
        yield readwrite_file, fname

def test02_modify():
    from numpy.random import randn
    data = randn(10000,nchan)
    with ewave.open(test_file,"w+",sampling_rate=Fs,dtype='f',nchannels=nchan) as fp:
        fp.write(data)
        d2 = fp.read(memmap='r+')
        assert_array_almost_equal(data,d2)
        d2 *= 2
        assert_array_almost_equal(data*2,d2)

    with ewave.open(test_file,"r") as fp:
        d2 = fp.read(memmap='r')
        assert_array_almost_equal(data*2,d2)

def test02_append():
    from numpy import random, concatenate
    d1 = random.randn(100,nchan)
    d2 = random.randn(100,nchan)
    with ewave.open(test_file,"w+",sampling_rate=Fs,dtype='f',nchannels=nchan) as fp:
        fp.write(d1)
        assert_array_almost_equal(d1,fp.read())
        fp.write(d2)
        assert_array_almost_equal(concatenate([d1,d2]),fp.read())

# Variables:
# End:

# -*- coding: utf-8 -*-
# -*- mode: python -*-
# Copyright (C) 2012 Dan Meliza <dan@meliza.org>
# Created Tue Aug 14 15:03:19 2012
import os
import glob
import unittest
from numpy.testing import assert_array_almost_equal

import ewave

test_dir = "test"
unsupported_dir = "unsupported"

# defaults for test file
test_file = None
nchan = 2
Fs = 48000


class TestEwave(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.wav")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def read_file(self, fname, memmap="r"):
        fp = ewave.open(fname, "r")
        self.assertEqual(fp.mode, "r")
        data = fp.read(memmap=memmap)
        if fp.nchannels == 1:
            self.assertEqual(data.ndim, 1)
            self.assertEqual(data.size, fp.nframes)
        else:
            self.assertEqual(data.shape[0], fp.nframes)
            self.assertEqual(data.shape[1], fp.nchannels)

    def write_file(self, fname, tgt_type=None):
        fp1 = ewave.open(fname, "r")
        with ewave.open(
            self.test_file,
            "w",
            sampling_rate=fp1.sampling_rate,
            dtype=tgt_type or fp1.dtype,
            nchannels=fp1.nchannels,
        ) as fp2:
            self.assertEqual(fp2.filename, self.test_file)
            self.assertEqual(fp2.sampling_rate, fp1.sampling_rate)
            self.assertEqual(fp2.nchannels, fp1.nchannels)
            if not tgt_type:
                self.assertEqual(fp2.dtype, fp1.dtype)
            fp2.write(fp1.read())
            self.assertEqual(fp2.nframes, fp1.nframes)
        os.remove(self.test_file)

    def readwrite_file(self, fname):
        """test files in r+ mode"""
        fp1 = ewave.open(fname, "r")
        d1 = fp1.read()
        with ewave.open(
            self.test_file,
            "w",
            sampling_rate=fp1.sampling_rate,
            dtype=fp1.dtype,
            nchannels=fp1.nchannels,
        ) as fp2:
            fp2.write(d1, scale=False).flush()

        with ewave.open(self.test_file, "r+") as fp3:
            self.assertEqual(fp3.filename, self.test_file)
            self.assertEqual(fp3.sampling_rate, fp1.sampling_rate)
            self.assertEqual(fp3.dtype, fp1.dtype)
            self.assertEqual(fp3.nchannels, fp1.nchannels)
            self.assertEqual(fp3.nframes, fp1.nframes)

            d2 = fp3.read(memmap="r+")
            assert_array_almost_equal(d1, d2)

        os.remove(self.test_file)

    def read_unsupported(self, fname):
        with self.assertRaises(ewave.Error):
            self.read_file(fname)

    def rescale(self, src_type, tgt_type):
        from numpy import ones, dtype

        d1 = ones(1000, dtype=src_type)
        if dtype(src_type).kind == "f":
            d1 *= 0.9
        d2 = ewave.rescale(d1, tgt_type)
        self.assertEqual(d2.dtype, dtype(tgt_type))

    # minor semantic checks
    def test00_mode(self):
        with self.assertRaises(ValueError):
            ewave.open(self.test_file, "a")

    def test00_handle(self):
        fp = open(self.test_file, "wb")
        with ewave.open(fp, sampling_rate=Fs, nchannels=nchan) as wfp:
            self.assertEqual(wfp.sampling_rate, Fs)
            self.assertEqual(wfp.filename, self.test_file)
        os.remove(self.test_file)

    def test00_invalidtype(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        try:
            ewave.open(self.test_file, "w", dtype="S2")
        except ewave.Error:
            # verify that file was not created
            self.assertFalse(
                os.path.exists(self.test_file), "file was created for invalid type"
            )
            return
        raise Exception("Exception was not raised for invalid type")

    def test00_intformat(self):
        """integer types stored as WAVE_FORMAT_PCM"""
        from numpy import zeros

        dtype = "i"
        data = zeros(1000, dtype=dtype)
        fp = open(self.test_file, "wb")
        with ewave.open(fp, dtype=dtype, sampling_rate=Fs, nchannels=nchan) as wfp:
            wfp.write(data)
        fp.close()
        with ewave.open(self.test_file, "r") as rfp:
            self.assertEqual(rfp._tag, ewave.WAVE_FORMAT_PCM)

    def test00_floatformat(self):
        """float types stored as WAVE_FORMAT_IEEE_FLOAT"""
        from numpy import zeros

        dtype = "f"
        data = zeros(1000, dtype=dtype)
        fp = open(self.test_file, "wb")
        with ewave.open(fp, dtype=dtype, sampling_rate=Fs, nchannels=nchan) as wfp:
            wfp.write(data)
        fp.close()
        with ewave.open(self.test_file, "r") as rfp:
            self.assertEqual(rfp._tag, ewave.WAVE_FORMAT_IEEE_FLOAT)

    def test00_rescalebad(self):
        with self.assertRaises(ewave.Error):
            ewave.rescale([1, 2, 3], "S2")

    # behavior checks
    def test01_rescaletypes(self):
        dtypes = ("u1", "h", "i", "l", "f", "d")
        for src in dtypes:
            for tgt in dtypes:
                self.rescale(src, tgt)

    # tests rescaling at edges
    def test01_rescalevalues(self):
        from numpy import array

        tests = (
            (32767, "h", 1 - 1 / (1 << 15)),
            (32768, "h", -1.0),
            ((1 << 31) - 1, "i", 1 - 1 / (1 << 31)),
            (1 << 31, "i", -1.0),
        )
        for val, dtype, expected in tests:
            self.assertAlmostEqual(ewave.rescale(array([val], dtype), "f")[0], expected)

    def test01_clipping(self):
        self.assertAlmostEqual(ewave.rescale(ewave.rescale([-1.01], "h"), "f")[0], -1.0)
        self.assertAlmostEqual(ewave.rescale(ewave.rescale([1.01], "i"), "f")[0], 1.0)

    def test01_read(self):
        for mmap in (False, "c", "r"):
            for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
                self.read_file(fname, mmap)

    def test01_unsupported(self):
        for fname in glob.iglob(os.path.join(unsupported_dir, "*.wav")):
            self.read_unsupported(fname)

    def test01_write(self):
        for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
            self.write_file(fname)

    def test01_convert(self):
        for tgt_type in ("f", "h"):
            for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
                self.write_file(fname, tgt_type)

    def test01_readwrite(self):
        for fname in glob.iglob(os.path.join(test_dir, "*.wav")):
            self.readwrite_file(fname)

    def test02_modify(self):
        from numpy.random import randn

        data = randn(10000, nchan)
        with ewave.open(
            self.test_file, "w+", sampling_rate=Fs, dtype="f", nchannels=nchan
        ) as fp:
            fp.write(data)
            d2 = fp.read(memmap="r+")
            assert_array_almost_equal(data, d2)
            d2 *= 2
            assert_array_almost_equal(data * 2, d2)

        with ewave.open(self.test_file, "r") as fp:
            d2 = fp.read(memmap="r")
            assert_array_almost_equal(data * 2, d2)

    def test02_append(self):
        from numpy import random, concatenate

        d1 = random.randn(100, nchan)
        d2 = random.randn(100, nchan)
        with ewave.open(
            self.test_file, "w+", sampling_rate=Fs, dtype="f", nchannels=nchan
        ) as fp:
            fp.write(d1)
            assert_array_almost_equal(d1, fp.read())
            fp.write(d2)
            assert_array_almost_equal(concatenate([d1, d2]), fp.read())


# Variables:
# End:

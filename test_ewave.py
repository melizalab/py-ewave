# -*- mode: python -*-
# Copyright (C) 2012 Dan Meliza <dan@meliza.org>
# Created Tue Aug 14 15:03:19 2012
import sys
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal

import ewave

test_dir = Path("test")
unsupported_dir = Path("unsupported")

# defaults for test file
test_file = None
nchan = 2
Fs = 48000


@pytest.fixture
def tmp_file(tmp_path):
    return tmp_path / "test.wav"


@pytest.fixture
def test_files():
    return test_dir.glob("*.wav")


@pytest.fixture
def unsupported_files():
    return unsupported_dir.glob("*.wav")


def rescale(src_type, tgt_type):
    from numpy import dtype, ones

    d1 = ones(1000, dtype=src_type)
    if dtype(src_type).kind == "f":
        d1 *= 0.9
    d2 = ewave.rescale(d1, tgt_type)
    assert d2.dtype == dtype(tgt_type)


def test00_invalid_mode(tmp_file):
    with pytest.raises(ValueError):
        ewave.open(tmp_file, "a")


def test01_create_file_from_handle(tmp_file):
    fp = open(tmp_file, "wb")
    with ewave.open(fp, sampling_rate=Fs, nchannels=nchan) as wfp:
        assert wfp.sampling_rate == Fs
        assert wfp.filename == str(tmp_file)


def test02_invalid_dtype(tmp_file):
    with pytest.raises(ewave.Error):
        ewave.open(tmp_file, "w", dtype="S2")
    assert not tmp_file.exists(), "file was created for invalid type"


def test03_create_int_format(tmp_file):
    """integer types stored as WAVE_FORMAT_PCM"""
    from numpy import zeros

    dtype = "i"
    data = zeros(1000, dtype=dtype)
    with ewave.open(
        tmp_file, mode="w", dtype=dtype, sampling_rate=Fs, nchannels=nchan
    ) as wfp:
        wfp.write(data)
    with ewave.open(tmp_file, "r") as rfp:
        assert rfp._tag == ewave.WAVE_FORMAT_PCM


def test04_create_float_format(tmp_file):
    """float types stored as WAVE_FORMAT_IEEE_FLOAT"""
    from numpy import zeros

    dtype = "f"
    data = zeros(1000, dtype=dtype)
    with ewave.open(
        tmp_file, "w", dtype=dtype, sampling_rate=Fs, nchannels=nchan
    ) as wfp:
        wfp.write(data)
    with ewave.open(tmp_file, "r") as rfp:
        assert rfp._tag == ewave.WAVE_FORMAT_IEEE_FLOAT


def test05_rescale_invalid_dtype():
    with pytest.raises(ewave.Error):
        ewave.rescale([1, 2, 3], "S2")


def test06_rescaletypes():
    dtypes = ("u1", "h", "i", "l", "f", "d")
    for src in dtypes:
        for tgt in dtypes:
            rescale(src, tgt)


def test07_rescalevalues():
    tests = (
        (32767, "h", 1 - 1 / (1 << 15)),
        (32768, "h", -1.0),
        ((1 << 31) - 1, "i", 1 - 1 / (1 << 31)),
        (1 << 31, "i", -1.0),
    )
    for val, dtype, expected in tests:
        rescaled = ewave.rescale(np.array([val]).astype(dtype), "f")[0]
        assert rescaled == pytest.approx(expected)


def test08_clipping():
    assert ewave.rescale(ewave.rescale([-1.01], "h"), "f")[0] == pytest.approx(-1.0)
    assert ewave.rescale(ewave.rescale([1.01], "i"), "f")[0] == pytest.approx(1.0)


def test09_read_examples_nomemmap(test_files):
    for fname in test_files:
        with ewave.open(fname, "r") as fp:
            assert fp.mode == "r"
            data = fp.read(memmap=False)
            if fp.nchannels == 1:
                assert data.ndim == 1
                assert data.size == fp.nframes
            else:
                assert data.shape[0] == fp.nframes
                assert data.shape[1] == fp.nchannels


# @pytest.mark.skipif(sys.platform == "win32", reason="memmap not supported on windows")
def test09_read_examples_memmap(test_files):
    for mmap in ("c", "r"):
        for fname in test_files:
            with ewave.open(fname, "r") as fp:
                assert fp.mode == "r"
                data = fp.read(memmap=mmap)
                if fp.nchannels == 1:
                    assert data.ndim == 1
                    assert data.size == fp.nframes
                else:
                    assert data.shape[0] == fp.nframes
                    assert data.shape[1] == fp.nchannels


def test10_open_unsupported(unsupported_files):
    for fname in unsupported_files:
        with pytest.raises(ewave.Error):
            _ = ewave.open(fname, "r")


def test11_write_examples(tmp_file):
    for fname in test_dir.glob("*.wav"):
        with ewave.open(fname, "r") as ifp, ewave.open(
            tmp_file,
            "w",
            sampling_rate=ifp.sampling_rate,
            dtype=ifp.dtype,
            nchannels=ifp.nchannels,
        ) as ofp:
            assert ofp.filename == str(tmp_file)
            assert ofp.sampling_rate == ifp.sampling_rate
            assert ofp.nchannels == ifp.nchannels
            assert ofp.dtype == ifp.dtype
            ofp.write(ifp.read())
            assert ofp.nframes == ifp.nframes


def test12_convert(tmp_file, test_files):
    for tgt_type in ("f", "h"):
        for fname in test_files:
            with ewave.open(fname, "r") as ifp, ewave.open(
                tmp_file,
                "w",
                sampling_rate=ifp.sampling_rate,
                dtype=tgt_type,
                nchannels=ifp.nchannels,
            ) as ofp:
                assert ofp.filename == str(tmp_file)
                assert ofp.sampling_rate == ifp.sampling_rate
                assert ofp.nchannels == ifp.nchannels
                assert ofp.dtype == tgt_type
                ofp.write(ifp.read())
                assert ofp.nframes == ifp.nframes


@pytest.mark.skipif(sys.platform == "win32", reason="memmap not supported on windows")
def test13_readwrite(tmp_file):
    for fname in test_dir.glob("*.wav"):
        with ewave.open(fname, "r") as ifp:
            d1 = ifp.read()
            with ewave.open(
                tmp_file,
                "w",
                sampling_rate=ifp.sampling_rate,
                dtype=ifp.dtype,
                nchannels=ifp.nchannels,
            ) as ofp:
                ofp.write(d1, scale=False).flush()

            with ewave.open(tmp_file, "r+") as rfp:
                assert rfp.filename == str(tmp_file)
                assert rfp.sampling_rate == ifp.sampling_rate
                assert rfp.dtype == ifp.dtype
                assert rfp.nchannels == ifp.nchannels
                assert rfp.nframes == ifp.nframes

                d2 = rfp.read(memmap="r+")
                assert_array_almost_equal(d1, d2)


@pytest.mark.skipif(sys.platform == "win32", reason="memmap not supported on windows")
def test14_modify_with_memmap(tmp_file):
    data = np.random.randn(10000, nchan)
    with ewave.open(tmp_file, "w+", sampling_rate=Fs, dtype="f", nchannels=nchan) as fp:
        fp.write(data)
        d2 = fp.read(memmap="r+")
        assert_array_almost_equal(data, d2)
        d2 *= 2
        assert_array_almost_equal(data * 2, d2)

    with ewave.open(tmp_file, "r") as fp:
        d2 = fp.read(memmap="r")
        assert_array_almost_equal(data * 2, d2)


def test15_append(tmp_file):
    d1 = np.random.randn(100, nchan)
    d2 = np.random.randn(100, nchan)
    with ewave.open(tmp_file, "w+", sampling_rate=Fs, dtype="f", nchannels=nchan) as fp:
        fp.write(d1)
        result = fp.read(memmap=False)
        assert_array_almost_equal(d1, result)
        fp.write(d2)
        result = fp.read(memmap=False)
        assert_array_almost_equal(np.concatenate([d1, d2]), result)


def test16_read_from_zip(tmp_path):
    from zipfile import ZipFile

    wav_name = "test.wav"
    tmp_file = tmp_path / wav_name
    tmp_zip = tmp_path / "test.zip"
    src_data = np.random.randn(10000, nchan)
    with ewave.open(tmp_file, "w+", sampling_rate=Fs, dtype="f", nchannels=nchan) as fp:
        fp.write(src_data)

    with ZipFile(tmp_zip, "w") as archive:
        archive.write(tmp_file, arcname=wav_name)

    with ZipFile(tmp_zip, "r") as archive:
        with archive.open(wav_name) as zipped_wave:
            with ewave.open(zipped_wave, "r") as fp:
                assert fp.sampling_rate == Fs
                assert fp.nchannels == nchan
                dst_data = fp.read(memmap=False)
                assert_array_almost_equal(src_data, dst_data)


# Variables:
# End:

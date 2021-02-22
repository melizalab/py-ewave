# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
Read and write WAVE format files.

Differences from wave.py in the python standard library (on which much of this
is based):

* Support is provided for reading and writing standard and extended format files
  with 8, 16, 32, or 64-bit linear PCM encoding, or with 32 or 64-bit IEEE float
  encoding.

* Data access is through numpy.memmap whenever possible. This speeds reading
  large files and allows files to be edited in place, by opening a file in 'r+'
  mode and calling read() with memmap='r+'; appending also works in this mode,
  as long as the data chunk is the last in the file. Files opened in 'w+' mode
  can be read after writing.

* A single class handles both read and write operations.

* Non-accessor methods can be chained, e.g. fp.write(data).flush()

Note that WAV files cannot store more than 2-4 GiB of data. Mu-law, A-law, and
other exotic encoding schemes are not supported. Does not support bit packings
where the container sizes don't correspond to mmapable types (e.g. 24 bit). Try
libsndfile for those sorts of files.

Copyright (C) 2012-2021 Dan Meliza <dan // AT // meliza.org>

"""
from __future__ import division
from __future__ import unicode_literals
WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

__version__ = "1.0.6"

class Error(Exception):
    pass


class wavfile(object):

    def __init__(self, file, mode='r', sampling_rate=20000, dtype='h', nchannels=1, **kwargs):
        """Opens a file for reading and/or writing.

        file:          the path of the file to open, or an open file-like object
        mode:          the mode to open the file (r, r+, w, w+). If already open,
                       uses the file's handle.
        sampling_rate: for 'w' mode only, set the sampling rate of the data
        dtype:         for 'w' mode only, set the storage format using one of the following codes:
                       'b','h','i','l':  8,16,32,64-bit PCM
                       'f','d':  32,64-bit IEEE float
        nchannels:     for 'w' mode only, set the number of channels to store

        additional keyword arguments are ignored

        The returned object may be used as a context manager, and will close the
        underlying file when the context exits.

        """
        import sys
        from builtins import open
        from numpy import dtype as ndtype
        # validate arguments; props are overwritten if header is read
        self._dtype = ndtype(dtype)
        self._nchannels = int(nchannels)
        self._framerate = int(sampling_rate)
        self._file_format(self._dtype)

        if hasattr(file, 'read'):
            self.fp = file
        else:
            if mode not in ('r', 'r+', 'w', 'w+'):
                raise ValueError("Invalid mode (use 'r', 'r+', 'w', 'w+')")
            self.fp = open(file, mode=mode + 'b')

        if self.mode == 'r':
            self._load_header()
        elif self.mode == 'r+':
            try:
                self._load_header()
            except EOFError:
                # file is empty; needs header
                self._write_header(sampling_rate, dtype, nchannels)
        else:
            self._write_header(sampling_rate, dtype, nchannels)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        if hasattr(self, 'fp') and hasattr(self.fp, 'close'):
            self.flush()
            self.fp.close()
            del self.fp

    @property
    def filename(self):
        """The path of the file """
        return self.fp.name

    @property
    def mode(self):
        """The mode for the file """
        return self.fp.mode.replace('b', '')

    @property
    def sampling_rate(self):
        return self._framerate

    @property
    def nchannels(self):
        return self._nchannels

    @property
    def nframes(self):
        if hasattr(self, "_bytes_written"):
            nbytes = self._bytes_written
        else:
            nbytes = self._data_chunk.getsize()
        return nbytes // (self.dtype.itemsize * self.nchannels)

    @property
    def dtype(self):
        """Data storage type """
        return self._dtype

    def __repr__(self):
        return "<open %s.%s '%s', mode '%s', dtype '%s', sampling rate %d at %s>" % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.filename,
            self.mode,
            self.dtype,
            self.sampling_rate,
            hex(id(self)))

    def flush(self):
        """Flushes data to disk and update header with correct size information """
        import struct
        if self.mode == 'r':
            return
        self.fp.seek(4)
        self.fp.write(
            struct.pack(b"<L", self._data_offset + self._bytes_written - 8))
        self.fp.seek(self._data_offset - 4)
        self.fp.write(struct.pack(b"<L", self._bytes_written))
        self.fp.flush()
        return self

    def read(self, frames=None, offset=0, memmap='c'):
        """Returns acoustic data from file.

        By default, the returned value is a memmap of the data in
        'copy-on-write' mode, which means read operations are delayed until the
        data are actually accessed or modified, and changes to the memmap object
        are not propagated to the disk.

        For multichannel WAV files, the data are returned as a 2D
        array with dimensions frames x channels

        - frames: number of frames to return. None for all the frames in the file
        - offset: start read at specific frame
        - memmap: if False, reads the whole file into memory at once; if not, returns
                  a numpy.memmap object using this value as the mode argument. 'c'
                  corresponds to copy-on-write; use 'r+' to write changes to disk. Be
                  warned that 'w' modes may corrupt data.

        """
        from numpy import memmap as mmap
        from numpy import fromfile
        if self.mode == 'w':
            raise Error('file is write-only')
        if self.mode in ('r+', 'w+'):
            self.fp.flush()
        # find offset
        coff = self._data_offset + offset * self.nchannels * self._dtype.itemsize
        if frames is None:
            frames = self.nframes - offset
        if memmap:
            A = mmap(self.fp, offset=coff, dtype=self._dtype, mode=memmap,
                     shape=frames * self.nchannels)
        else:
            pos = self.fp.tell()
            self.fp.seek(coff)
            A = fromfile(
                self.fp, dtype=self._dtype, count=frames * self.nchannels)
            self.fp.seek(pos)

        if self.nchannels > 1:
            nsamples = (A.size // self.nchannels) * self.nchannels
            A = A[:nsamples]
            A.shape = (nsamples // self.nchannels, self.nchannels)
        return A

    def write(self, data, scale=True):
        """Writes data to the WAVE file

        - data : input data, in any form that can be converted to an array with
                 the file's dtype. Data are silently coerced into an array whose
                 shape matches the number of channels in the file.

        - scale : if True, data are rescaled so that their maximum range matches
                    that of the file's encoding. If not, the raw values are
                    used, which can result in clipping.
        """
        from numpy import asarray
        if self.mode == 'r':
            raise Error('file is read-only')
        if hasattr(self, '_postdata_chunk') and self._postdata_chunk:
            raise Error('cannot append to data chunk without overwriting other chunks')

        if not scale:
            data = asarray(data, self._dtype)
        data = rescale(data, self._dtype).tostring()

        self.fp.write(data)
        self._bytes_written += len(data)
        return self

    def _load_header(self):
        """Reads metadata from header """
        from numpy import dtype
        from chunk import Chunk
        import struct

        fp = Chunk(self.fp, bigendian=0)
        if fp.getname() != b'RIFF':
            raise Error('file does not start with RIFF id')
        if fp.read(4) != b'WAVE':
            raise Error('not a WAVE file')
        self._fmt_chunk = None
        self._fact_chunk = None
        self._data_chunk = None
        self._postdata_chunk = None
        while 1:
            try:
                chunk = Chunk(fp, bigendian=0)
            except EOFError:
                break
            chunkname = chunk.getname()
            if chunkname == b'fmt ':
                self._fmt_chunk = chunk
            elif chunkname == b'fact':
                self._fact_chunk = chunk
            elif chunkname == b'data':
                if not self._fmt_chunk:
                    raise Error('data chunk before fmt chunk')
                self._data_chunk = chunk
            elif self._data_chunk and self._fact_chunk:
                # check whether a chunk is present after the data chunk to
                # prevent appending data
                self._postdata_chunk = chunk
            chunk.skip()
        if not self._fmt_chunk or not self._data_chunk:
            raise Error("fmt and/or data chunk missing")

        self._dtype = None
        self._fmt_chunk.seek(0)
        self._tag, self._nchannels, self._framerate, nAvgBytesPerSec, wBlockAlign, bits = \
            struct.unpack(b'<HHLLHH', self._fmt_chunk.read(16))
        # load extended block if it's there
        if self._tag == WAVE_FORMAT_EXTENSIBLE:
            if self._fmt_chunk.getsize() < 16:
                raise Error('extensible format but no format extension')
            cbSize, wValidBits, dwChannelMask, self._tag = \
                struct.unpack(b'<hhlH', self._fmt_chunk.read(10))
        if self._tag == WAVE_FORMAT_PCM:
            # bit size is rounded up to the nearest multiple of 8; I'm
            # not going to support any format that can't be easily
            # mmap'd, i.e. files that have weird container sizes (like 24)
            if bits <= 8:
                self._dtype = dtype('B')
            elif bits <= 16:
                self._dtype = dtype('<h')
            elif bits <= 24:
                raise Error("unsupported bit depth: %d" % bits)
            elif bits <= 32:
                self._dtype = dtype('<i')
            elif bits == 64:
                self._dtype = dtype('<l')
            else:
                raise Error("unsupported bit depth: %d" % bits)
        elif self._tag == WAVE_FORMAT_IEEE_FLOAT:
            try:
                self._dtype = dtype('float%d' % bits)
            except:
                raise Error("unsupported bit depth for IEEE floats: %d" % bits)
        else:
            raise Error('unsupported format: %r' % (self._tag,))
        self._data_offset = self._data_chunk.offset + 8
        if self.mode == "r+":
            self.fp.seek(0, 2)
            self._bytes_written = self.fp.tell() - self._data_offset

    @classmethod
    def _file_format(cls, dtype):
        """Returns appropriate file format or raises an error """
        if dtype.kind == 'i' or (dtype.kind == 'u' and dtype.itemsize == 1):
            return WAVE_FORMAT_PCM
        elif dtype.kind == 'f':
            return WAVE_FORMAT_IEEE_FLOAT
        else:
            raise Error("unsupported type %r cannot be stored in wave files" % dtype)

    def _write_header(self, sampling_rate, dtype, nchannels, write_fact=None):
        """Creates header for wave file based on sampling rate and data type """
        # this is a bit tricky b/c Chunk is a read-only class
        # however, this only gets called for a pristine file
        # we'll have to go back and patch up the sizes later
        import struct
        # main chunk
        out = struct.pack(b'<4sl4s', b'RIFF', 0, b'WAVE')
        # fmt chunk
        tag = etag = self._file_format(self._dtype)
        fmt_size = 16
        if self._dtype.itemsize > 2 or self._nchannels > 2:
            fmt_size = 40
            tag = WAVE_FORMAT_EXTENSIBLE

        out += struct.pack(b'<4slHHllHH',
                           b'fmt ', fmt_size, tag, self._nchannels, self._framerate,
                           self._nchannels * self._framerate *
                           self._dtype.itemsize,
                           self._nchannels * self._dtype.itemsize,
                           self._dtype.itemsize * 8)

        if tag == WAVE_FORMAT_EXTENSIBLE:
            out += struct.pack(b'<HHlH14s', 22,
                               self._dtype.itemsize * 8,
                               # use the full bitdepth
                               (1 << self._nchannels) - 1,
                               etag,
                               b'\x00\x00\x00\x00\x10\x00\x80\x00\x00\xaa\x008\x9b\x71')

        # fact chunk
        if write_fact or (write_fact is None and tag in (WAVE_FORMAT_IEEE_FLOAT,
                                                         WAVE_FORMAT_EXTENSIBLE)):
            out += struct.pack(b"<4sll", b"fact", 4, self._dtype.itemsize)
        # beginning of data chunk
        out += struct.pack(b"<4sl", b"data", 0)

        self.fp.seek(0)
        self.fp.write(out)
        self._data_offset = self.fp.tell()
        self._bytes_written = 0

open = wavfile


def rescale(data, tgt_dtype):
    """Rescales data to the correct range for tgt_dtype.

    - data: a numpy array or anything convertable into one.
    - tgt_dtype: the data type of the target container
    """
    from numpy import asarray, dtype, minimum, maximum
    # convert to numpy array, retaining best type
    data = asarray(data)
    src = data.dtype
    tgt = dtype(tgt_dtype)
    if src == tgt:
        return data

    if tgt.kind == 'f':
        if src.kind == 'f':
            return data.astype(tgt)
        umax = 1 << (src.itemsize * 8 - 1)
        out = (data / umax).astype(tgt)
        if src.kind == 'u':
            out -= 1.0
        return out

    elif src.kind == 'f' and tgt.kind in ('i', 'u'):
        umax = 1 << (tgt.itemsize * 8 - 1)
        out = data * umax
        # assume positive clipping - may break on other architectures
        out = minimum(maximum(out, -umax), umax - 1).astype(tgt)

    elif tgt.kind in ('i', 'u'):
        if tgt > src:
            out = (data.astype(tgt) << (tgt.itemsize - src.itemsize) * 8)
        else:
            out = (data >> (src.itemsize - tgt.itemsize) * 8).astype(tgt)
    else:
        raise Error("unsupported target type %r" % tgt)

    if src.kind != tgt.kind and src.kind == 'u' or tgt.kind == 'u':
        out += asarray(1, dtype=tgt) << tgt.itemsize * 8 - 1

    return out


# Variables:
# End:

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
  large files and allows files to be edited in place (open in 'a' mode)

* A single class handles both read and write operations.
  
Note that WAV files cannot store more than 2-4 GiB of data. Only read support is
provided for extensible format WAVE files.

Copyright (C) 2012 Dan Meliza <dan // AT // meliza.org>
Created 2012-03-29
"""

class Error(Exception):
    pass

WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

def open(f, *args, **kwargs):
    """ Open a file for reading and/or writing. Any of the standard modes
    supported by file can be used.

    f:             the path of the file to open, or an open file-like object
    mode:          the mode to open the file. if already open, uses the file's handle
    sampling_rate: for 'w' mode only, set the sampling rate of the data
    dtype:         for 'w' mode only, set the storage format using one of the following codes:
                   'b','h','i','l':  8,16,32,64-bit PCM
                   'f','d':  32,64-bit IEEE float
    nchannels:     for 'w' mode only, set the number of channels to store
    """
    return wavfile(f, *args, **kwargs)

class wavfile(object):
    def __init__(self, f, mode='r', sampling_rate=20000, dtype='h', nchannels=1):
        if isinstance(f, basestring):
            if mode not in ('r','r+','w','a'):
                raise ValueError, "Invalid mode (use 'r', 'r+', 'w', or 'a')"
            self.fp = file(f, mode=mode+'b')
        else:
            self.fp = f

        if self.mode[0] in ('r','a'):
            self._load_header()
        else:
            self._make_header(sampling_rate, dtype, nchannels)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return exc_val

    @property
    def filename(self):
        """ The path of the file """
        return self.fp.name

    @property
    def mode(self):
        """ The mode for the file """
        m = self.fp.mode
        return m[:m.find('b')]

    @property
    def sampling_rate(self):
        return self._framerate

    @property
    def nchannels(self):
        return self._nchannels

    @property
    def channels(self):
        if self.nchannels == 1: return ('pcm',)
        else: return ('left','right')
        # add support for > 2 channels

    @property
    def nframes(self):
        nbytes = self._data_chunk.getsize()
        return nbytes // (self.dtype.itemsize * self.nchannels)

    @property
    def dtype(self):
        """ Data storage type """
        return self._dtype

    def close(self):
        """ Close the file handle and sets modification/access time """
        if hasattr(self,'fp') and hasattr(self.fp,'close'): self.fp.close()

    def _load_header(self):
        """ Read metadata from header """
        from numpy import dtype
        from chunk import Chunk
        import struct
        
        fp = Chunk(self.fp, bigendian=0)
        if fp.getname() != 'RIFF':
            raise Error, 'file does not start with RIFF id'
        if fp.read(4) != 'WAVE':
            raise Error, 'not a WAVE file'
        self._fmt_chunk = None
        self._fact_chunk = None
        self._data_chunk = None
        while 1:
            try:
                chunk = Chunk(fp, bigendian=0)
            except EOFError:
                break
            chunkname = chunk.getname()
            if chunkname == 'fmt ':
                self._fmt_chunk = chunk
            elif chunkname == 'fact':
                self._fact_chunk = chunk
            elif chunkname == 'data':
                if not self._fmt_chunk:
                    raise Error, 'data chunk before fmt chunk'
                self._data_chunk = chunk
                break
            chunk.skip()
        if not self._fmt_chunk or not self._data_chunk:
            raise Error, "fmt and/or data chunk missing"

        self._dtype = None
        self._fmt_chunk.seek(0)
        wFormatTag, self._nchannels, self._framerate, nAvgBytesPerSec, wBlockAlign, bits = \
            struct.unpack('<HHLLHH', self._fmt_chunk.read(16))
        # load extended block if it's there
        if wFormatTag == WAVE_FORMAT_EXTENSIBLE:
            if self._fmt_chunk.getsize() < 16:
                raise Error, 'extensible format but no format extension'
            cbSize,wValidBits,dwChannelMask,wFormatTag = \
                struct.unpack('<hhlH',self._fmt_chunk.read(10))
        if wFormatTag == WAVE_FORMAT_PCM:
            # bit size is rounded up to the nearest multiple of 8; I'm
            # not going to support any format that can't be easily
            # mmap'd, i.e. files that have weird container sizes (like 24)
            if bits <= 8:
                self._dtype = dtype('B')
            elif bits <= 16:
                self._dtype = dtype('<h')
            elif bits <= 24:
                raise Error, "invalid bits per sample: %d" % bits
            elif bits <= 32:
                self._dtype = dtype('<i')
            elif bits == 64:
                self._dtype = dtype('<l')
            else:
                raise Error, "invalid bits per sample: %d" % bits
        elif wFormatTag == WAVE_FORMAT_IEEE_FLOAT:
            try:
                self._dtype = dtype('float%d' % bits)
            except:
                raise Error, "unsupported bit depth for IEEE floats: %d" % bits
        else:
            raise Error, 'unsupported format: %r' % (wFormatTag,)


    def _make_header(self, sampling_rate, dtype, nchannels):
        """ Create header for wave file based on sampling rate and data type """
        # this is a bit tricky b/c Chunk is a read-only class
        # however, this only gets called for a pristine file
        # we'll have to go back and patch up the sizes later
        from numpy import dtype as ndtype
        import struct

        # main chunk
        out = struct.pack('4s<l4s','RIFF',0,'WAVE')

        # fmt chunk
        self._dtype = ndtype(dtype)
        self._nchannels = int(nchannels)
        self._framerate = int(sampling_rate)
        fmt_size = 16
        if self._dtype.kind == 'i':
            if self._dtype.itemsize <= 2:
                tag = WAVE_FORMAT_PCM
            else:
                tag = WAVE_FORMAT_EXTENSIBLE
                fmt_size += 22
        elif self._dtype.kind == 'f':
            tag = WAVE_FORMAT_IEEE_FLOAT
        else:
            raise Error, "unsupported type %r cannot be stored in wave files" % self._dtype

        out += struct.pack('4slhhllhh',
                           'fmt ', fmt_size, tag, self._nchannels, self._framerate,
                           self._nchannels * self._framerate * self._dtype.itemsize,
                           self._nchannels * self._dtype.itemsize,
                           self._dtype.itemsize * 8)
        if tag == WAVE_FORMAT_EXTENSIBLE:
            pass

        
    def read(self, frames=None, offset=0, memmap='c'):
        """
        Return contents of file. Default is is to memmap the data in
        copy-on-write mode, which means read operations are delayed
        until the data are actually accessed or modified.

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
        # find offset
        coff = self._data_chunk.offset + 8 + offset * self.nchannels * self._dtype.itemsize
        if frames is None: frames = self.nframes - offset
        if memmap:
            A = mmap(self.fp, offset=coff, dtype=self._dtype, mode=memmap,
                     shape=frames*self.nchannels)
        else:
            pos = self.fp.tell()
            self.fp.seek(coff)
            A = fromfile(self.fp, dtype=self._dtype, count=frames*self.nchannels)
            self.fp.seek(pos)

        if self.nchannels > 1:
            nsamples = (A.size // self.nchannels) * self.nchannels
            A = A[:nsamples]
            A.shape = (nsamples // self.nchannels, self.nchannels)
        return A
            
    def write(self, data):
        """
        Write data to the WAV file. Not supported for files opened in
        read mode.

        data: input data, in any form that can be converted to an
              array with an appropriate data type.
        """
        from numpy import asarray
        if self.mode=='r':
            raise Error, 'file is read-only'

        data = nx.asarray(data, self._dtype)
        self.fp.writeframes(data.tostring())

        
# Variables:
# End:

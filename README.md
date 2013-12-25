## ewave

Pure python support for reading and writing extended WAVE formats.

The wave module in Python's standard library is old and doesn't support a number
of useful formats and encodings, notably IEEE floats. Ewave is a small, simple
solution written in pure Python that provides a number of enhanced features:

-   Floating point formats
-   Extensible formats (> 2 channels, larger bit depths)
-   Read and write using memory mapping for simple, speedy access to large files
-   Read directly to numpy arrays
-   Data appended to existing files in read/write modes can be immediately accessed
-   Rescaling of data for different encodings and bit depths
-   Supports Python context managers for cleaner resource semantics

### Requirements and installation

Ewave requires Python 2.6+ or 3.2+ and numpy 1.0+.

To install, run `python setup.py install` in the source directory, or
`pip install ewave`. Because numpy is a large installation, it's not installed
automatically; run `pip install numpy` if you don't already have it.

### Usage

There are some notable differences between the ewave interface and the standard
library wave module. There's only a single class that manages both reading and
writing, and a number of the properties have changed names and behaviors.
Importantly, the read method by default returns a numpy memmap to the data in
the file. This provides faster access to large files and allows writing data in
place.

For example, to write a second of stereo white noise in floating point format
and then rescale it in place:

```python
import ewave
from numpy import random
data = random.randn(48000,2)
with ewave.open("myfile.wav","w+",sampling_rate=48000,dtype='f',nchannels=2) as fp:
    fp.write(data)
    # rescale the data by 50%
    fp.read(memmap='r+') *= 0.5
```

### Testing

Ewave has been tested on a large number of different WAVE formats and comes with
a fairly extensive unit test suite.  To run unit tests on files, place them in
the 'test' subdirectory and run `nosetests`.  You can also place unsupported or
invalid files in the 'unsupported' directory to test whether ewave rejects them
correctly.  Bug reports are always appreciated.

### Limitations and related projects

'Exotic' encodings like A-law and mu-law are not supported.  Formats in which
the container size (the bit depth) does not align with a native data type,
including some 24-bit formats, are not supported.  Data cannot be appended to
files that terminate in something other than a data chunk, and multiple data
chunks are not supported.

Users interested in access to more complex WAVE and non-WAVE files and who do not
mind external library dependencies should consider one of these wrappers to
libsndfile:

-   <http://code.google.com/p/libsndfile-python/>
-   <http://www.ar.media.kyoto-u.ac.jp/members/david/softwares/audiolab/>

### Licence and acknowledgements

Ewave is based heavily on the original wave module in the Python standard
library and is released under the same Python Software Foundation Licence
(<http://opensource.org/licenses/python-2.0>)

Information about the WAVE formats supported by this module was extensively
gleaned from
<http://www-mmsp.ece.mcgill.ca/documents/audioformats/wave/wave.html>.

[![Build Status](https://travis-ci.org/melizalab/py-ewave.png?branch=master)](https://travis-ci.org/melizalab/py-ewave)

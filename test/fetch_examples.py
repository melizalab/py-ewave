#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
# Copyright (C) 2013 Dan Meliza <dan@meliza.org>
import os
import posixpath as pp
import subprocess

base_url = "http://www-mmsp.ece.mcgill.ca/documents/audioformats/wave/Samples"
files = ["AFsp/M1F1-uint8-AFsp.wav",
         "AFsp/M1F1-int16-AFsp.wav",
         "AFsp/M1F1-int16WE-AFsp.wav",
         "AFsp/M1F1-int32-AFsp.wav",
         "AFsp/M1F1-int32WE-AFsp.wav",
         "AFsp/M1F1-float32-AFsp.wav",
         "AFsp/M1F1-float64WE-AFsp.wav",
         "Microsoft/6_Channel_ID.wav"]

if __name__ == "__main__":

    for f in files:
        cmd = "curl %s -o %s" % (pp.join(base_url, f), os.path.join("test", pp.basename(f)))
        subprocess.call(cmd.split())


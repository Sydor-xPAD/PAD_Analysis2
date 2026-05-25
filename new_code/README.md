new_code
========

This directory contains utilities for various analyses and tests of the xPAD cameras.  The directory `xpad_process` contains a utility for format conversion and simple image corrections.

`padstack.py`
-------------

This file contains the code for the format conversion and image corrections.  It is called by `analyze_xpad.py`, described below.  Take note of variable `FRAME_DIAGNOSTICS` in `padstack.py`; the code it controls can be built on to extract the histograms used for debouncing.

`xpad_process`
--------------

This directory separates an analysis utility from the underlying libraries.  The main program is `analyze_xpad.py`, which can convert raw images into HDF5 files and perform some corrections.  It outputs both a file of rasters and an HDF5 file.  See `xpad_process/README_HDF5.md` for more details.
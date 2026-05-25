xPAD Processed File Usage
=========================

The image processing utilities have the possiblity of saving images in an HDF5 file.  This file may be loaded by other utilities.

Fiji
====

Fiji, a distribution of ImageJ, includes a plugin for loading HDF5 files.  To open an HDF5 file in Fiji, go to the menu bar and select Plugins&gt;HDF5&gt;Load HDF5 File..., then select the file.  The image data are stored in dataset `image`.

Octave
======

Octave may be used to load the image data from an HDF5 file.  The command is `load(<HDF5 file>, 'image')`  This will load the data into variable name `image`  The matrix is transposed, with dimensions `(width, height, num_images)`.

Resources
=========

* Fiji: [https://fiji.sc](https://fiji.sc)
* ImageJ: [https://imagej.net/software/imagej/](https://imagej.net/software/imagej/)
* Octave: [https://octave.org](https://octave.org)
* Python: [https://www.python.org](https://python.org)
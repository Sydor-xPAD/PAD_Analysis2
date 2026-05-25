import numpy as np
import sys
import os
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import padstack

## Here we load two files for the foreground and background images.
## rtsup outputs images into files of 1000 images each.  These inidividual
## files can be concatenated into one big file.
## PADStack has a third argument of `file_type`, which by default is
## 'IMG' to load a PAD image file.  Other options are 'FF' for a flatfield
## file and 'DEFECT' to load and combine a pair of hot and dark masks.

fg_img = padstack.PADStack("/mnt/raid/mmpad/set-GlassyC_2026-04-15/run-foreb_0010f_100usexp_015usif/frames/foreb_0010f_100usexp_015usif_00000001.raw", "MMPAD");

bg_img = padstack.PADStack("/mnt/raid/mmpad/set-GlassyC_2026-04-15/run-back_0010f_100usexp_015usif/frames/back_0010f_100usexp_015usif_00000001.raw", "MMPAD");


## This prints out some statistics
print("fg: images: {}, caps {},size {}".format(fg_img.numImages, fg_img.numCaps, fg_img.imgStack[0].shape))

print("bg: images: {}, caps {},size {}".format(bg_img.numImages, bg_img.numCaps, bg_img.imgStack[0].shape))

## This coalesces the stack into a background frame (or frames, in the case of
## KeckPAD.)  The argument is how many initial frames to skip in computing
## the background image.  The first frame of an MMPAD run is often invalid, so
## keep that in mind if concatenating images as described above.  By default,
## two frames are skipped.

bg_img.computeBgStack(2);

## Print statistics on the computed background image
print("bg: images: {}, caps {},size {}".format(bg_img.numImages, bg_img.numCaps, bg_img.imgStack[0].shape))

## Perform the background subtraction, leaving the results in fg_img.  
fg_img.bgSub(bg_img);


## Perform a debounce.  For this instance, the number of bins in the histogram
## used for the debounce is altered.  The histogram limits are in fg_img.histBinStart and fg_img.histBinEnd, defaulting to (-200,800).  1000 bins makes each bin 1 ADU wide, versus the default of 200 bins for 5 ADU bin width.
fg_img.numBins=1000
fg_img.apply_debounce();

## Threading without the global interpreter lock has been implemented.
## This performs a print showing the if GIL has been re-enabled.  These lines
## are only applicable for Python version >= 3.13
print("Check GIL")
print(sys._is_gil_enabled())

## Geocorrect the images using the threaded implementation.  This will work
## even if the GIL is enabled.  The argument is the location of the geocal
## file.  There must be no comments in the file, and the submodules must be
## in order from 0 on up.
fg_img.geocorr_truethread("/home/iainm/temp/xPAD00013/gc_params.cfg")

## Here we save the image as a series of double rasters in a raw binary format.
out_file = open("glassyc.img", "wb");

for image_frame in fg_img.imgStack:
    image_frame.tofile(out_file)

out_file.close()

## Save the image and metadata in an HDF5 file.  The image raster is in dataset
## `image`
fg_img.saveImg("glassyc.hdf5")


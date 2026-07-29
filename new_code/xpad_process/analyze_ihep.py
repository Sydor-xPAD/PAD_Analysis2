import numpy as np
import sys
import os
import inspect
import matplotlib.pyplot as plt
import matplotlib
import scipy
import math

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

#fg_img = padstack.PADStack("ihep_raw/run-TiZaNbTa-30us/frames/TiZaNbTa-30us_00000001.raw", "KECKPADX2");
#fg_img_ndb = padstack.PADStack("ihep_raw/run-TiZaNbTa-30us/frames/TiZaNbTa-30us_00000001.raw", "KECKPADX2");
#bg_img = padstack.PADStack("ihep_raw/run-TiZaNbTa-30us-bkg/frames/TiZaNbTa-30us-bkg_00000001.raw", "KECKPADX2");

#bg_img = padstack.PADStack("/mnt/raid/mmpad/set-GlassyC_2026-04-15/run-back4_1e3f_1e5usexp_015usif/frames/back4_1e3f_1e5usexp_015usif_00000001.raw", "MMPAD");

#fg_img = padstack.PADStack("ihep_raw/run-testrun-10ms-003/frames/testrun-10ms-003_00000001.raw", "KECKPADX2");
#fg_img_ndb = padstack.PADStack("ihep_raw/run-testrun-10ms-003/frames/testrun-10ms-003_00000001.raw", "KECKPADX2");
#bg_img = padstack.PADStack("ihep_raw/run-testrun-10ms-003-backg/frames/testrun-10ms-003-backg_00000001.raw", "KECKPADX2");

fg_img = padstack.PADStack("ihep_raw/run-s175_h2o-50us-dyncom-long-006/frames/s175_h2o-50us-dyncom-long-006_00000001.raw", "KECKPADX2");
fg_img_ndb = padstack.PADStack("ihep_raw/run-s175_h2o-50us-dyncom-long-006/frames/s175_h2o-50us-dyncom-long-006_00000001.raw", "KECKPADX2");
bg_img = padstack.PADStack("ihep_raw/run-s175_h2o-50us-backg-new/frames/s175_h2o-50us-backg-new_00000001.raw", "KECKPADX2");

#fg_img = padstack.PADStack("ihep_raw/run-ni#3-danjing-dynamic-2-20us/frames/ni#3-danjing-dynamic-2-20us_00000001.raw", "KECKPADX2");
#fg_img_ndb = padstack.PADStack("ihep_raw/run-ni#3-danjing-dynamic-2-20us/frames/ni#3-danjing-dynamic-2-20us_00000001.raw", "KECKPADX2");
#bg_img = padstack.PADStack("ihep_raw/run-background-20us/frames/background-20us_00000001.raw", "KECKPADX2");

flat_image = padstack.PADStack("ihep_config/etc/xPAD00015/flatfield.raw", "KECKPADX2", "FF")

happyimg = padstack.PADStack("happymask.pgm", "KECKPADX2", "SINGLEMASK")

## This prints out some statistics
print("fg: images: {}, caps {},size {}".format(fg_img.numImages, fg_img.numCaps, fg_img.imgStack[0].shape))

print("bg: images: {}, caps {},size {}".format(bg_img.numImages, bg_img.numCaps, bg_img.imgStack[0].shape))

## This coalesces the stack into a background frame (or frames, in the case of
## KeckPAD.)  The argument is how many initial frames to skip in computing
## the background image.  The first frame of an MMPAD run is often invalid, so
## keep that in mind if concatenating images as described above.  By default,
## two frames are skipped.

bg_img.computeBgStack(2);

#bg_img.saveImg("back_ihep.hdf5")

## Print statistics on the computed background image
print("bg: images: {}, caps {},size {}".format(bg_img.numImages, bg_img.numCaps, bg_img.imgStack[0].shape))

## Perform the background subtraction, leaving the results in fg_img.  
fg_img.bgSub(bg_img);
fg_img_ndb.bgSub(bg_img)

#fg_img.saveImg("bgsub_ihep.hdf5")

## Perform a debounce.  For this instance, the number of bins in the histogram
## used for the debounce is altered.  The histogram limits are in fg_img.histBinStart and fg_img.histBinEnd, defaulting to (-200,800).  1000 bins makes each bin 1 ADU wide, versus the default of 200 bins for 5 ADU bin width.
fg_img.histBinStart = -100
fg_img.histBinEnd = 200
fg_img.numBins = 75
#fg_img.numBins=200
fg_img.fpBound=(-75,75)
#fg_img.apply_debounce(MaskFilename="s175_mask.pgm");
fg_img.apply_debounce();

## Do the flatfield correction
#fg_img.applyFF(flat_image) 

# fg_img.augmentMask(happyimg);

## Threading without the global interpreter lock has been implemented.
## This performs a print showing the if GIL has been re-enabled.  These lines
## are only applicable for Python version >= 3.13
print("Check GIL")
print(sys._is_gil_enabled()
)
## Geocorrect the images using the threaded implementation.  This will work
## even if the GIL is enabled.  The argument is the location of the geocal
## file.  There must be no comments in the file, and the submodules must be
## in order from 0 on up.
fg_img.geocorr_truethread_kega("ihep_gc.cfg")
fg_img_ndb.geocorr_truethread_kega("ihep_gc.cfg")

## Here we save the image as a series of double rasters in a raw binary format.
#out_file = open("ihep_data.img", "wb");

#for image_frame in fg_img.imgStack:
#    image_frame.tofile(out_file)

#out_file.close()

## Save the image and metadata in an HDF5 file.  The image raster is in dataset
## `image`
fg_img.saveImgKega("s175mask_data.hdf5")
fg_img_ndb.saveImgKega("s175mask_ndb_data.hdf5")
bg_img.saveImgKega("s175mask_bg.hdf5")

## Now try a radial intensity

radial_center = (579,520)

bin_edges, sig_tot, num_counts = padstack.radial_intensity(fg_img.imgStack[1], radial_center, 400, (25.0*math.pi/180.0, 51.0*math.pi/180.0))

print(bin_edges.shape)
print(sig_tot.shape)

fig, ax = plt.subplots()
ax.stairs(sig_tot, bin_edges)
plt.savefig('raps.png')
plt.close(fig)

sys.exit(0)

entry_idx = -1
for entry in fg_img.asic_details:
    entry_idx += 1
    fig, ax  = plt.subplots()
    #ax.bar(entry[3][0:-1], entry[2],width=4, align='center')
    debounce_amount = fg_img.debounce_log[entry_idx][2]
    asic_med = fg_img.asic_stats[entry_idx][3]
    ax.stairs(entry[2],entry[3])
    ax.plot([debounce_amount, debounce_amount],[0,2000], 'r-')
    ax.plot([asic_med, asic_med],[0,2000], 'g-')
    ax.set_xlim(left=-50, right=200)
    modemed = asic_med-debounce_amount
    my_hist = np.extract(np.logical_and(np.greater_equal(entry[3][0:-1],-50),np.less_equal(entry[3][0:-1],150)), entry[2])
    midpoints = [(entry[3][i]+entry[3][i+1])/2 for i in range(len(my_hist))]
    #print(my_hist)
    #print(midpoints)
    raw_data = np.concatenate([np.full((count,),midpoint) for count, midpoint in zip(my_hist, midpoints)])
    asic_skew = scipy.stats.skew(raw_data)
    ax.text(-40,2000,"Diff: {}\nSkew: {}".format(modemed, asic_skew))
    asic_idx = entry[1]
    frame_idx = entry[0]

    plt.savefig('hist_{}_{}.png'.format(frame_idx, asic_idx))
    plt.close(fig)

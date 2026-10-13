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
## file, 'DEFECT' to load and combine a pair of hot and dark masks, and 'SINGLEMASK' to load a mask that should be applied to all images, versus the per-cap and paired nature of 'DEFECT'

fg_img = padstack.PADStack("/mnt/raid/mmpad/set-GlassyC_2026-04-15/run-glassyCc_f002_1e3f_1e5usexp_015usif/frames/glassyCc_f002_1e3f_1e5usexp_015usif_00000001.raw", "MMPAD")
bg_img = padstack.PADStack("/mnt/raid/mmpad/set-GlassyC_2026-04-15/run-back4_1e3f_1e5usexp_015usif/frames/back4_1e3f_1e5usexp_015usif_00000001.raw", "MMPAD");

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
#fg_img_ndb.bgSub(bg_img)

fg_img.saveImg("bgsub_glassyc.hdf5")

# At this point, we would apply the defect mask.  The first step is to load the masks:
defect_img = padstack.PADStack("/usr/local/etc/xPAD00013/", "MMPAD", "DEFECT")
# This will load /usr/local/etc/xPAD00013/hot_pixels.pgm and
# /usr/local/etc/xPAD00013/dark_pixels.pgm
## THE TRAILING SLASH in padstack.PADSTACK IS MANDATORY!

# Once the masks are loaded, we can apply them to the background-subtracted image stack.

fg_img.applyDefect(defect_img);

## Perform a debounce.  For this instance, the number of bins in the histogram
## used for the debounce is altered.  The histogram limits are in fg_img.histBinStart and fg_img.histBinEnd, defaulting to (-200,800).  1000 bins makes each bin 1 ADU wide, versus the default of 200 bins for 5 ADU bin width.
fg_img.histBinStart = -100
fg_img.histBinEnd = 200
fg_img.numBins = 75
#fg_img.numBins=200
fg_img.fpBound=(-75,75)

## There are some options available for debounce.  One is to use a mask with the dark regions non-zero; the median of these points will be used as the bounce value.

#fg_img.apply_debounce(MaskFilename="s175_mask.pgm");

## A second is to use a curve-fitting approach.  There are some different approaches in the code, but the first step is to use a topographic routine to find one or more peaks.  A quadratic fit can be performed on the first peak; this provides more accurate results when there is a spur in the histogram.  A new routine attempts to fit two Gaussian curves when there is only one distinct peak, as may happen if the source is not monochromatic.

fg_img.apply_debounce();

## With the bounce removed, there is no random offset, so the flatfield gain correction may be applied.  If using the factory default flatfield map, this step also implicity applies the defect map, as the defects are marked as bad pixels in the flatfield map.

## Do the flatfield correction
flat_image = padstack.PADStack("/usr/local/etc/xPAD00013/flatfield.raw", "MMPAD", "FF")
fg_img.applyFF(flat_image) 


## For some analyses, it may be useful to mask out regions of the image.  For example, in powder diffraction, there may be Laue spots, or a beam stop in the image.  The below marks the non-zero pixels in the mask as NaN.
mask_img = padstack.PADStack("experiment_mask.tiff", "MMPAD", "SINGLEMASK")
fg_img.augmentMask(mask_img)

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

fg_img.geocorr_truethread("/usr/local/etc/xPAD00013/gc_params.cfg")

## There are separate functions for geocorrection of regular-sized images (512Wx512H) and the larger half-MegaPAD (1024Wx512H)

#fg_img.geocorr_truethread_kega("ihep_gc.cfg")
#fg_img_ndb.geocorr_truethread_kega("ihep_gc.cfg")

## Here we save the image as a series of double rasters in a raw binary format.
out_file = open("mmpad_data.img", "wb");

for image_frame in fg_img.imgStack:
    image_frame.tofile(out_file)

out_file.close()

## Save the image and metadata in an HDF5 file.  The image raster is in dataset
## `image`
## Once again, there are separate saving routines for regular-sized images and half-MegaPAD-sized images.
fg_img.saveImg("glassyc_data.hdf5")
#fg_img_ndb.saveImgKega("s175mask_ndb_data.hdf5")
bg_img.saveImg("glassyc_bg.hdf5")

sys.exit(0)

## Some simple routines are provided for first looks at diffraction patters.  First is intensity as a function of radius.  This routine operates on a Numpy ndarray, and allows specifying start and stop angles in radians, always going counter-clockwise from the start angle to the end angle, and the angles in range [0,2pi].  The radii, total signal, and number of pixels contributing per radius are returned; this allows computing an average intensity per radius.

## Now try a radial intensity

radial_center = (579,520)

bin_edges, sig_tot, num_counts = padstack.radial_intensity(fg_img.imgStack[1], radial_center, 400, (25.0*math.pi/180.0, 51.0*math.pi/180.0))

## Do some plotting of the results
fig, ax = plt.subplots()
ax.stairs(sig_tot, bin_edges)
plt.savefig('raps.png')
plt.close(fig)


# We can also look at signal as a function of theta.  This function also operates on ndarrays.  Optional arguments are the angular start and stop 
bin_edges, sig_tot, num_counts = padstack.angular_intensity(fg_img.imgStack[1], radial_center, 800, abounds=(25.0*math.pi/180.0, 51.0*math.pi/180.0), det_dist=25000)

print(bin_edges.shape)
print(sig_tot.shape)

fig, ax = plt.subplots()
ax.stairs(sig_tot, bin_edges)
ax.set_ylim(0,1000)
plt.savefig('aaps.png')
plt.close(fig)

fig, ax = plt.subplots()
ax.stairs(sig_tot/num_counts, bin_edges,)
plt.savefig('aaps_mean.png')
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

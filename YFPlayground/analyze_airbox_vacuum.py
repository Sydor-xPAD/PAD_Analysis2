import padstack
import numpy as np
import sys

fg_img = padstack.PADStack("/mnt/raid/mmpad/set-GlassyC_2026-04-15/run-foreb_0010f_100usexp_015usif/frames/foreb_0010f_100usexp_015usif_00000001.raw", "MMPAD");

bg_img = padstack.PADStack("/mnt/raid/mmpad/set-GlassyC_2026-04-15/run-back_0010f_100usexp_015usif/frames/back_0010f_100usexp_015usif_00000001.raw", "MMPAD");


print("fg: images: {}, caps {},size {}".format(fg_img.numImages, fg_img.numCaps, fg_img.imgStack[0].shape))

print("bg: images: {}, caps {},size {}".format(bg_img.numImages, bg_img.numCaps, bg_img.imgStack[0].shape))

bg_img.computeBgStack(2);

print("bg: images: {}, caps {},size {}".format(bg_img.numImages, bg_img.numCaps, bg_img.imgStack[0].shape))

fg_img.bgSub(bg_img);

fg_img.numBins=1000
fg_img.apply_debounce();

print("Check GIL")
print(sys._is_gil_enabled())

fg_img.geocorr_truethread("/home/iainm/temp/xPAD00013/gc_params.cfg")

out_file = open("vaccuum_airbox_adaptive.img", "wb");

for image_frame in fg_img.imgStack:
    image_frame.tofile(out_file)

out_file.close()

fg_img.saveImg("vacuum_airbox.hdf5")


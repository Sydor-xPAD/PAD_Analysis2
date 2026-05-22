import os
import sys
# Add the directory to sys.path

sys.path.append(os.path.relpath('image-gener'))

import genimages
import genframes
import imagesensor
import numpy as np
import scipy
import matplotlib.pyplot as plt
import sys

def convert( in_filename , outfilename ):

    in_file = open(in_filename, "rb")

    test_sensor = imagesensor.Image_Sensor((512,512),(128,128))
    # test_sensor.gen_dark_map([123,1], 400, 10, 0.01)

    test_image = genimages.Camera_Image(test_sensor)

    num_frames = 0

    test_image.gen_frames(num_frames, 0, genframes.Image_Frame.gen_frame_from_file, [in_file])
    test_image.init_xpad_hdr_consts(genimages.eXpad_Sys_Type.ST_SYS_MMPAD);
    test_image.create_xpad_file(outfilename, genimages.eXpad_Pixel_Type.DT_UINT32, 1000)



if __name__ == "__main__":
    pass
    #convert( todo, todo)
    
import Big_keck_load as bkl
import sys

#img_file = open('mm-pad-512x512-2020-06-23-14-32-33-0001.raw', 'rb');
img_file = open(sys.argv[1], 'rb');

for frame_idx in range(10):
    payload = bkl.keckFrame(img_file);
    print("Cap Mask: {:03X}".format((payload[2][6]>>12) & 0x1ff));

img_file.close();

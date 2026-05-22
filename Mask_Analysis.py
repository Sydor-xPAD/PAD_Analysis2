import numpy as np
import Big_keck_load as BKL
import os
import pickle
import CreateSim
import configparser
import sys

class EventPixel:
    def __init__(self):
        self.x = -1;
        self.y = -1;
        self.cap = -1;
        self.value = -1;        # Initialize to invalid values

cfg_parser = configparser.ConfigParser()
cfg_parser.read("photon_mask.ini")

num_caps = int(cfg_parser['Default']['num_caps'])
Low = int(cfg_parser['Default']['low_neighbor_thresh'])
Hi = int(cfg_parser['Default']['high_neighbor_thresh'])
backImageFilename = cfg_parser['Default']['mask_check_bg_filename']
foreImageFilename = cfg_parser['Default']['mask_check_fg_filename']
image_width = int(cfg_parser['Default']['image_width'])
image_height = int(cfg_parser['Default']['image_height'])
sensor_bpp = int(cfg_parser['Default']['sensor_bpp'])
file_gap = int(cfg_parser['Default']['file_gap'])
file_offset = int(cfg_parser['Default']['file_offset'])
x_margin = int(cfg_parser['Default']['x_margin'])
y_margin = int(cfg_parser['Default']['y_margin'])
sys_type = cfg_parser['Default']['sys_type']

if sys_type == 'keckpad':
    load_func = BKL.keckFrame
elif sys_type == 'mmpad':
    load_func = BKL.mmpadFrame
else:
    print("Unrecognized system type: " + sys_type)
    sys.exit(1)
          

# Set thresholds
low_thresh = [Low, Low, Low, Low, Low, Low, Low, Low]; # Threshold for neighbors being low
high_thresh = [Hi, Hi, Hi, Hi, Hi, Hi, Hi, Hi]; # Threshold for pixel under test being high

# Allocate arrays
backStack = np.zeros((num_caps,image_height,image_width), dtype=np.double);
foreStack = np.zeros((num_caps,image_height,image_width), dtype=np.double);

# Load background
numBackImages = int(os.path.getsize(backImageFilename)/(file_gap+image_height*image_width*(sensor_bpp/8)))
backImageFile = open(backImageFilename, "rb");

for fIdx in range(numBackImages): 
    payload = BKL.keckFrame(backImageFile);
    backStack[(payload[3]-1)%num_caps,:,:] += np.resize(payload[4],[image_height,image_width]);
backStack = backStack/(numBackImages/num_caps); # Average the background
backImageFile.close();

# Load the foreground images
numForeImages = int(os.path.getsize(foreImageFilename)/(file_gap+image_height*image_width*sensor_bpp/8));
foreImageFile = open(foreImageFilename, "rb");

for fIdx in range(numForeImages):
    payload = BKL.keckFrame(foreImageFile);
    foreStack[(payload[3]-1)%num_caps,:,:] += np.resize(payload[4],[image_height,image_width]);
foreStack = foreStack/(numForeImages/num_caps); # Average the background
foreImageFile.close();

# Compute the background subtracted image
fmbImage = foreStack - backStack;

# Save the computed images
# Uncomment below if wish to save images
foreStack.tofile('fore_avg.raw');
backStack.tofile('back_avg.raw');
fmbImage.tofile('fmb.raw');

if False:
    simData = CreateSim.CreateSim()
    for x in range(8):
        fmbImage[x,:,:] = simData;

singlePixelList = [];
noPixelList = [];
total_pixels = 0;
cold_neighborhoods = 0;
    
#Now iterate over the inner pixels to find single events
for cap_idx in range(num_caps):
    curr_frame = fmbImage[cap_idx,:,:]; # Get just the current frame
    for row_idx in range(y_margin,image_height-y_margin):    # Ignore outer two pixels
        for col_idx in range(x_margin, image_width-x_margin): # Ibid
            total_pixels += 1;       # Increment pixel count
            test_mat = curr_frame[(row_idx-1):(row_idx+1+1),(col_idx-1):(col_idx+1+1)]; # Extract the 3x3 neighborhood
            # Compute the low threshold
            cold_test = (test_mat<low_thresh[cap_idx]).astype(int); # See if neighborhood below limi
            cold_test[1,1] = 0;              # Set inner to zero for sum
            cold_sum = np.sum(cold_test);
            #if (cold_sum > 0):
            #    print(cold_test);
            cold_neighbor = False;
            if cold_sum == 8:   # All pixels below threshold
                cold_neighbor = True;
                cold_neighborhoods += 1;
                test_pixel = EventPixel();
                test_pixel.x = col_idx;
                test_pixel.y = row_idx;
                test_pixel.cap = cap_idx;
                test_pixel.value = test_mat[1,1]; # Set the pixel parameters
                
                # Determine list to append to
                if test_pixel.value >= high_thresh[cap_idx]: # Pixel hot
                    singlePixelList.append(test_pixel);
                # uncomment below if you want to save no pixel list    
                # else:           # Pixel cold
                #     noPixelList.append(test_pixel);

print("Tested {} pixels.".format(total_pixels));
print("Cold neighborhoods: {}".format(cold_neighborhoods));
print("{} single pixels and {} no pixels.".format(len(singlePixelList),len(noPixelList)));
single_pixel_filename = 'single_pix.csv';
single_pixel_file = open(single_pixel_filename, 'w');
full_pixel_list = []
for curr_pixel in singlePixelList:
    single_pixel_file.write('{},{},{},{}\n'.format(curr_pixel.y, curr_pixel.x, curr_pixel.cap, curr_pixel.value));
    full_pixel_list.append(curr_pixel.value)
    #if (curr_pixel.y < 128) and (curr_pixel.x < 128) and (curr_pixel.cap == 3):
        #single_pixel_file.write('{},{},{},{}\n'.format(curr_pixel.y, curr_pixel.x, curr_pixel.cap, curr_pixel.value));
single_pixel_file.close();

full_pixel_list.sort()
num_pixels = len(full_pixel_list)
print("Histogram IQR: {}:{}".format(full_pixel_list[int(num_pixels*0.25)], full_pixel_list[int(num_pixels*0.75)]))

#uncomment below if you want to save no pixel list to file
# no_pixel_filename = 'no_pix.csv';
# no_pixel_file = open(no_pixel_filename, 'w');
# for curr_pixel in noPixelList:
#     no_pixel_file.write('{},{},{},{}\n'.format(curr_pixel.y, curr_pixel.x, curr_pixel.cap, curr_pixel.value));
# no_pixel_file.close();

# Pickle the results
pickleFile = open('pixels.pickle', 'wb')
pickle.dump(singlePixelList, pickleFile);
pickle.dump(noPixelList, pickleFile);
pickleFile.close();

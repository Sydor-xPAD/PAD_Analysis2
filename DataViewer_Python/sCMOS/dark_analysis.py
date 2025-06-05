import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import linregress
import re 
import os

# SET STUFF UP 
#dir_name = 'C:/SydorInstruments/DataViewer_7rc3/release/';                
dir_name = 'C:/data/darkdata/low1/'; # Val's directory name
filename_prefix = 'neg25_low_';     # The prefix of the foreground files
filename_count = 6;             # How many foreground files in a set
filename_suffix = '.raw';       # The extension after the filename
img_size = [2048, 2048];        # Height, width
roi_start = [512, 512];         # y,x
roi_size = [1024, 1024];        # Height, width
bg_filename = 'back/' + filename_prefix + '0s.raw'; # The name of the background file


# make a file list 
dark_list = [];
for x in os.listdir():
    if x.endswith(filename_suffix);
    x = dark_list
print(dark_list)

for x in os.listdir():
    if x.endswith(".txt"):



# get a list of the integration times from the file name
time_list = []
for fname in dark_list:
    parts = fname.split('_')
    inttime = parts[len(parts)-1].split('s')[0]
    time_list.append(inttime)
print(time_list)





# Load the background image
bg_img = np.fromfile(bg_filename, np.ushort, img_size[0]*img_size[1]);
bg_img = bg_img.reshape(img_size[0], img_size[1]);
bg_img = bg_img.astype(np.double);

# Create the result arrays
burst_array = np.array(burst_count_list);
mean_array = np.array(np.arange(filename_count));
std_array = np.array(np.arange(filename_count));
# Now iterate over all images
for file_idx, curr_filename in enumerate(filename_list):
    # Load the image
    fg_img = np.fromfile(curr_filename, np.ushort, img_size[0]*img_size[1]);
    fg_img = fg_img.reshape(img_size[0], img_size[1]);
    fg_img = fg_img.astype(np.double);
    
    # BG Sub and ROI extract
    sub_img = fg_img-bg_img;
    # display the last back subtracted file
    if curr_filename == filename_list[filename_count-3]:
       X =np.arange(0, 2048, 1)
       Y = np.arange(0, 2048, 1)
       Z = sub_img
       data = plt.imshow(Z, interpolation ='nearest', origin ='lower')
       plt.xlabel('horizontal pixel number')
       plt.ylabel('vertical pixel number')
       plt.title(curr_filename)
       plt.colorbar(data)
       plt.savefig(dir_name + 'sampleflatfield')
       plt.close()
    
    roi_img = sub_img[roi_start[0]:(roi_start[0]+roi_size[0]), roi_start[1]:(roi_start[1]+roi_size[1])];

    #-=-= Debugging
    #roi_img.tofile("back_roi.raw");

    # Compute the statistics
    img_mean = roi_img.mean();
    img_std = roi_img.std();
    mean_array[file_idx] = img_mean;
    std_array[file_idx] = img_std;
    
# Print statistics for manual verification
print("Burst Counts:");
print(burst_array);
print("\nImage Means:");
print(mean_array);
print("\nImage Std Dev:");
print(std_array);

# plot mean vs number of pulses
plt.plot(burst_array, mean_array, marker='o', markersize=8, markerfacecolor='black', ls='None', label='image average')
plt.xlabel('number of bursts')
plt.ylabel('ADU')
plt.title('mean ADU with increasing LED pulses')

#plt.ylim(1,8)
plt.xlim(0,(burst_count + 1))

slope, intercept, r_value, p_value, std_err = linregress(burst_array, mean_array)
print(slope, intercept, r_value)
line = slope*burst_array+intercept
plt.plot(burst_array, line, 'r', label= 'y={:.2f}x+{:.2f}, R2={:.2f}'.format(slope,intercept, r_value))
plt.legend(fontsize=9)

plt.savefig(dir_name+'lin_graph.png', bbox_inches='tight')
#plt.show();
plt.close()




import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import linregress
import statistics 

#dir_name = 'C:/SydorInstruments/DataViewer_7rc3/release/';                

dir_name = 'C:/data/linearitydata/lowG4/';
filename_prefix = 'Burst_';     # The prefix of the foreground files
filename_count = 18;             # How many foreground files in a set
filename_suffix = '.raw';       # The extension after the filename
burst_interval = 4;          # Step count of bursts
img_size = [2048, 2048];        # Height, width
roi_start = [1000, 1000];         # y,x
roi_size = [512, 512];        # Height, width
bg_filename = dir_name + 'back2.raw'; # The name of the background file

filename_list = [];
burst_count_list = [];
for filename_idx in range(filename_count):
    burst_count = (filename_idx + 1) * burst_interval;
    burst_count_list.append(burst_count);
    filename_list.append(dir_name + filename_prefix + '{}'.format(burst_count) + filename_suffix);

# Load the background image
bg_img = np.fromfile(bg_filename, np.ushort, img_size[0]*img_size[1]);
bg_img = bg_img.reshape(img_size[0], img_size[1]);
bg_img = bg_img.astype(np.double);

# Create the result arrays
burst_array = np.array(burst_count_list);
mean_array = np.array(np.arange(filename_count));
std_array = np.array(np.arange(filename_count));
var_array = np.array(np.arange(filename_count));
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
    img_var = statistics.variance(roi_img.flatten(), xbar=None);
    mean_array[file_idx] = img_mean;
    std_array[file_idx] = img_std;
    var_array[file_idx] = img_var;
    
# Print statistics for manual verification
print("Burst Counts:");
print(burst_array);
print("\nImage Means:");
print(mean_array);
print("\nImage Std Dev:");
print(std_array);
print("\nImage Variance:");
print(var_array);

# Now create the plots
#fig,axs = plt.subplots(3,1);
#axs[0].plot(burst_array, mean_array)
#axs[0].set_title('Mean vs Bursts');
#axs[1].plot(burst_array, std_array);
#axs[1].set_title('StdDev vs Bursts');
#axs[2].scatter(mean_array, std_array);
#axs[2].set_title('StdDev vs Mean')

# # band-aid
# mean_array = mean_array[0:11]
# var_array = var_array[0:11]
# std_array = std_array[0:11]

plt.plot(burst_array, mean_array, marker='o', markersize=8, markerfacecolor='black', ls='None', label='image average')
plt.xlabel('number of bursts')
plt.ylabel('ADU')
plt.title('mean ADU with increasing LED pulses')

#plt.ylim(1,8)
#plt.xlim(0,(burst_count + 1))

slope, intercept, r_value, p_value, std_err = linregress(burst_array, mean_array)
print(slope, intercept, r_value)
line = slope*burst_array+intercept
plt.plot(burst_array, line, 'r', label= 'y={:.2f}x+{:.2f}, R2={:.2f}'.format(slope,intercept, r_value))
plt.legend(fontsize=9)

plt.savefig(dir_name+'lin_graph.png', bbox_inches='tight')
#plt.show();
plt.close()

# make a plot of mean vs variance 
plt.plot(mean_array, var_array, marker='o', markersize=8, markerfacecolor='black', ls='None', label='image average')
plt.xlabel('mean')
plt.ylabel('variance')
plt.title('Gain Plot')

slope, intercept, r_value, p_value, std_err = linregress(mean_array, var_array)
print(slope, intercept, r_value)
line = slope*mean_array+intercept
plt.plot(mean_array, line, 'r', label= 'y={:.2f}x+{:.2f}, R2={:.2f}'.format(slope,intercept, r_value))
plt.legend(fontsize=9)

plt.savefig(dir_name + 'linearity.png', bbox_inches='tight')
#plt.show();
#plt.close();



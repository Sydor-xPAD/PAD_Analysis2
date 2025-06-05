import numpy as np
from matplotlib import pyplot as plt
import glob
import sys

def time_sort(time_val):        # Just get the exposure time for sorting
    return time_val[0];         # Exp time is first element in tuple

dir_name = 'C:/data/darkdata/highG_dark_0/';                # The location of the dark files
# Filenames assume for now a format of '*_<exposure time>.raw'
filename_prefix = 'neg25_low_'; # The prefix of the dark files
filename_suffix = '.raw';        # The extension after the filename
img_size = [2048, 2048];         # Height, width
roi_start = [512, 512];          # y,x
roi_size = [1024, 1024];         # Height, width
default_gain = 1.0;              # Fallback ADU/e- if not otherwise specfied
units_adu = False;                # Whether to provide Y-axis as ADU or e-

# The filenames are assembled by globbing for the exposure time
raw_filename_list = glob.glob(dir_name + filename_prefix + '[0-9]*' +filename_suffix);
print("Analyzing {} files.".format(len(raw_filename_list)));
if (len(raw_filename_list) == 0):
    print("No files found.");
    sys.exit(1)

actual_gain = 1.0;
if '_high_' in filename_prefix:
    actual_gain = 1.83;         # ADU/e-
    print('High gain detected: conversion {:.3f} ADU/e-'.format(actual_gain));
elif '_low_' in filename_prefix:
    actual_gain = 0.078;        # ADU/e-
    print('Low gain detected: conversion {:.3f} ADU/e-'.format(actual_gain));
else:
    actual_gain = default_gain; # Fallback to default
    print('No gain detected.  Using default {:.3f} ADU/e-'.format(actual_gain));

y_label = '';                   # Create label for later plot
if units_adu:
    print('Using ADU.');
    actual_gain = 1.0;          # No conversion, so set gain to 1.0
    y_label = 'Mean (ADU)';
else:
    print('Using e-');
    y_label = 'Mean (e-)';

    
filename_list = [];
exp_times = [];
# Now sort the files by exposure time
for curr_filename in raw_filename_list:
    raw_time_str = curr_filename.split('_')[-1].split('.')[0]; #extract the text time
    time_str = raw_time_str.replace('p', '.');                 # Change to decimmal point
    time_str = time_str.rstrip('s');
    curr_time = float(time_str)*1; # Convert to ms with *1000 if not already in ms
    exp_times.append((curr_time, curr_filename));

# Sort in ascending exposure time
exp_times.sort(key=time_sort);

bg_img = np.ndarray(img_size)*0; # Create default background array
#See if there is an actual background image
if exp_times[0][0] == 0:        # Zero second exposure time is BG
    print("Background image detected.");
    bg_filename = exp_times[0][1]; # Get the filename
    bg_img = np.fromfile(bg_filename, np.ushort); # Load image
    bg_img = bg_img.reshape(-1, img_size[0], img_size[1]); # Reshape
    bg_img = np.mean(bg_img, axis=0);                      # Average over frames
    exp_times = exp_times[1:];      # Skip the zero entry XXX Assumes only one BG image
bg_img = bg_img[roi_start[0]:(roi_start[0]+roi_size[0]), roi_start[1]:(roi_start[1]+roi_size[1])]; # Extract the ROI


time_log = [];
avg_log = [];                   # Store the results of the computations
for curr_entry in exp_times:
    time_log.append(curr_entry[0]);
    curr_filename = curr_entry[1];
    curr_img = np.fromfile(curr_filename, np.ushort); # Load image
    curr_img = curr_img.reshape(-1, img_size[0], img_size[1]); # Reshape

    #print('Curr image shape:');
    #print(curr_img.shape)
    roi_img = curr_img[:,roi_start[0]:(roi_start[0]+roi_size[0]), roi_start[1]:(roi_start[1]+roi_size[1])];
    #print('ROI image shape:');
    #print(roi_img.shape);
    avg_img = np.mean(roi_img, axis=0); # Average slices first for future expansion
    avg_img = avg_img - bg_img;         # Subtract the background
    curr_mean = np.mean(avg_img);
    curr_mean = curr_mean/actual_gain; # Convert from ADC
    avg_log.append(curr_mean)

time_log = np.array(time_log);
avg_log = np.array(avg_log);

lin_fit = np.polyfit(time_log, avg_log, 1);

fit_times = np.array([time_log[0], time_log[-1]]);
fit_line = fit_times*lin_fit[0]+lin_fit[1];

fig, axs = plt.subplots(1,1);
l_sig, = axs.plot(time_log, avg_log, '-o')
l_fit, = axs.plot(fit_times, fit_line, '--');
axs.set_title('{}\n{:.3f}x+{:.3f}'.format(filename_prefix, lin_fit[0], lin_fit[1]));
axs.set_xlabel('Time (ms)');
axs.set_ylabel(y_label);
axs.legend((l_sig, l_fit), ('Measured', 'Fit'), loc='lower right', shadow=True);
axs.grid(True);
fig.savefig('linearity.png');
plt.show()

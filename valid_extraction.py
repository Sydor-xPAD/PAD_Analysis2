import MaskExtract
import os
import numpy as np
import matplotlib.pyplot as plt
import Big_keck_load as BKL
import CreateSim
import math
import pickle
import sys
import configparser
from scipy.optimize import curve_fit
import glob

cfg_parser = configparser.ConfigParser()
cfg_parser.read("photon_mask.ini")

fit_max_eval = int(cfg_parser['Default']['fit_max_eval'])
bgFilename = cfg_parser['Default']['hist_bg_filename']
fgGlobPattern = cfg_parser['Default']['hist_fg_globpattern']
maskFilename = cfg_parser['Default']['mask_filename']
image_width = int(cfg_parser['Default']['image_width'])
image_height = int(cfg_parser['Default']['image_height'])
num_caps = int(cfg_parser['Default']['num_caps'])
file_offset = int(cfg_parser['Default']['file_offset'])
file_gap = int(cfg_parser['Default']['file_gap'])
sensor_bpp = int(cfg_parser['Default']['sensor_bpp'])

sys_type = cfg_parser['Default']['sys_type']
if sys_type == 'keckpad':
    load_func = BKL.keckFrame
elif sys_type == 'mmpad':
    load_func = BKL.mmpadFrame
else:
    print("Unrecognized system type: " + sys_type)
    sys.exit(1)

clipPos = int(cfg_parser['Default']['clip_pos'])
clipNeg = int(cfg_parser['Default']['clip_neg'])
clip_thresh = float(cfg_parser['Default']['clip_thresh'])
hist_bin_min = int(cfg_parser['Default']['hist_bin_min'])
hist_bin_max = int(cfg_parser['Default']['hist_bin_max'])

fit_invoke = 0;
def twoGauss(xdata, a, b, c, d, e, f, g):
    global fit_invoke;
    fit_invoke += 1;
    #print(fit_invoke, a, b, c, d, e, f, g);
    result_y = np.arange(xdata.size).astype(np.double);
    for x_idx in range(xdata.size):
        x = xdata[x_idx];
        result_y[x_idx] = a * math.exp(-0.5*((x-b)/c)**2) + d * math.exp(-0.5*((x-e)/f)**2) + g;
    #print(xdata, result_y)
    return result_y;

def threeGauss(xdata, a, b, c, d, e, f, g, j, k, l):
    global fit_invoke;
    fit_invoke += 1;
    #print(fit_invoke, a, b, c, d, e, f, g, j, k, l);
    result_y = np.arange(xdata.size).astype(np.double);
    for x_idx in range(xdata.size):
        x = xdata[x_idx];
        result_y[x_idx] = a * math.exp(-0.5*((x-b)/c)**2) + \
        d * math.exp(-0.5*((x-e)/f)**2) + \
            g * math.exp(-0.5*((x-j)/k)**2) + l;
    #print(xdata, result_y)
    return result_y;

def fourGauss(xdata, a, b, c, d, e, f, g, j, k, l, m, n, o):
    global fit_invoke;
    fit_invoke += 1;
    #print(fit_invoke, a, b, c, d, e, f, g, j, k, l);
    result_y = np.arange(xdata.size).astype(np.double);
    for x_idx in range(xdata.size):
        x = xdata[x_idx];
        result_y[x_idx] = a * math.exp(-0.5*((x-b)/c)**2) + \
        d * math.exp(-0.5*((x-e)/f)**2) + \
            g * math.exp(-0.5*((x-j)/k)**2) + \
                l * math.exp(-0.5*((x-m)/n)**2) + o;
    #print(xdata, result_y)
    return result_y;

def fiveGauss(xdata, a, b, c, d, e, f, g, j, k, l, m, n, o, p, q, r):
    global fit_invoke;
    fit_invoke += 1;
    #print(fit_invoke, a, b, c, d, e, f, g, j, k, l);
    result_y = np.arange(xdata.size).astype(np.double);
    for x_idx in range(xdata.size):
        x = xdata[x_idx];
        result_y[x_idx] = a * math.exp(-0.5*((x-b)/c)**2) + \
        d * math.exp(-0.5*((x-e)/f)**2) + \
            g * math.exp(-0.5*((x-j)/k)**2) + \
                l * math.exp(-0.5*((x-m)/n)**2) + \
                    o * math.exp(-0.5*((x-p)/q)**2) + r
    #print(xdata, result_y)
    return result_y;



def clip_hist(hist_data, clip_thresh):
    hist_data.sort();
    num_valid = len(hist_data);
    clipped_pixels = hist_data[int(num_valid*clip_thresh):int((num_valid*(1-clip_thresh))+1)];
    return clipped_pixels;

b_mode_sel = False
test_mode = False
analysis_mode = False
num_peaks = 0
if len(sys.argv) == 2:
    if sys.argv[1] == "-t":
        print("Test Mode selected.")
        test_mode = True
        b_mode_sel = True
elif len(sys.argv) == 3:
    if sys.argv[1] == "-a":
        num_peaks = int(sys.argv[2])
        if (num_peaks >= 3) and (num_peaks <= 5):
            analysis_mode = True
            b_mode_sel = True


if not b_mode_sel:
    print("Usage: python3 valid_extraction.py {-t|-a <# Peaks>}")
    sys.exit(1)
    

# Specify the number of caps
CAP_LIMIT = num_caps            # Start by iterating over all caps
if test_mode:
    CAP_LIMIT = 1               # Only test first cap if in test mode
    
pFolder = "vref_50kv"
dFolder = "vref"

backImageData = open(bgFilename,"rb")

backStack = np.zeros((num_caps,image_height,image_width),dtype=np.double)
numImages = int(os.path.getsize(bgFilename)/(file_gap+image_height*image_width*sensor_bpp/8))

#Calc cap backs
for fIdex in range(numImages):
   payload = load_func(backImageData)
   backStack[(payload[3]-1)%num_caps,:,:] += np.resize(payload[4],[image_height,image_width])
backStack = backStack/ (numImages/num_caps)


# Initialize the extractor
pixelExtractor = MaskExtract.MaskExtractor();
pixelExtractor.load_mask(maskFilename);
pixelExtractor.singlePixelMat = pixelExtractor.singlePixelMat[:,:,:] # [caps, y1:y2, x1:x2]


fg_filelist = glob.glob(fgGlobPattern)
for fgFilename in fg_filelist:
    # Iterate over all foreground images
    fgImageFile = open(fgFilename, "rb");
    numFgImages = int(os.path.getsize(fgFilename)/(file_gap+image_height*image_width*sensor_bpp/2));


    for fIdx in range(numFgImages):
        payload = load_func(fgImageFile);
        curr_frame = payload[4].reshape([image_height,image_width]);
        fmbImg = curr_frame - backStack[(payload[3]-1)%num_caps,:,:];

        pixelExtractor.extract_frame(fmbImg, (payload[3]-1)%num_caps); # FIXME Assumes that all caps are being used in the foreground image
        
    # Close the file
    fgImageFile.close();

# Now get some valid pixels
valid_pixels = [];
for cap_idx in range(num_caps):
    valid_pixels.append(np.array(pixelExtractor.valid_values[cap_idx]).astype(np.double))

# Clip the arrays
clipped_pixels = [];
for cap_idx in range(num_caps):
    clipped_pixels.append(clip_hist(valid_pixels[cap_idx], clip_thresh));

# Now histogram the arrays
hist_pixels = [];
# binRan = np.arange(-50,351);    # The bins for the histogram
binRan = np.arange(hist_bin_min,hist_bin_max);


for cap_idx in range(num_caps):
    hist_pixels.append((np.histogram(clipped_pixels[cap_idx], bins=binRan))[0]);

# # Now do the curve fitting
# Initialize the results arrays
guess_array = [[],[],[]]
fit_pixels = [[],[],[]]
fit_params = [[],[],[]]
# Figure out which functions we will try
b_three_peak = True
b_four_peak = True
b_five_peak = True
if not test_mode:             # Change based on analysis mode
    b_three_peak = (num_peaks == 3)
    b_four_peak = (num_peaks == 4)
    b_five_peak = (num_peaks == 5)

    
for cap_idx in range(CAP_LIMIT):
# #   # Two Gauss
#     guess_val = [ 1, 0, 10, 0.9, 30, 10, 0];
#     guess_val[0] = np.max(hist_pixels);
#     guess_val[3] = guess_val[0]*0.9;
    
    # Three Gauss
    guess_val = [1, 0, 10, 0.9, 30, 10, 0.5, 60, 10, 0]
    guess_val[0] = np.max(hist_pixels)
    guess_val[3] = guess_val[0]*0.9
    guess_val[6] = guess_val[0]*0.5;
    
    guess_array[0] = guess_val

    #     # Four Gauss
    guess_val = [1, 0, 10, 0.9, 30, 10, 0.5, 60, 10, 0.2, 90, 10, 0]
    guess_val[0] = np.max(hist_pixels)
    guess_val[3] = guess_val[0]*0.9
    guess_val[6] = guess_val[0]*0.5
    guess_val[9] = guess_val[0]*0.5;

    guess_array[1] = guess_val

    #     # Five Gauss
    guess_val = [1, 0, 10, 0.9, 30, 10, 0.5, 60, 10, 0.2, 90, 10, 0.1, 120, 10, 0]
    guess_val[0] = np.max(hist_pixels)
    guess_val[3] = guess_val[0]*0.9
    guess_val[6] = guess_val[0]*0.5
    guess_val[9] = guess_val[0]*0.5
    guess_val[12] = guess_val[0] *0.5

    guess_array[2] = guess_val

    # Prepare for output
    mean_index = []             # A list of indices containing the means of peaks
    sigma_index = []            # A list of indices containing the sigmas of peaks
    
#     # Two Gauss
#     fit_vals = curve_fit(twoGauss, binRan[:-1], hist_pixels[cap_idx], guess_val, method='dogbox');
#     fit_pixels.append(twoGauss(binRan[:-1], *fit_vals[0]));

    # Three Gauss
    if b_three_peak:
        fit_vals = curve_fit(threeGauss, binRan[:-1], hist_pixels[cap_idx], guess_array[0], method='dogbox', max_nfev=fit_max_eval);
        fit_pixels[0].append(threeGauss(binRan[:-1], *fit_vals[0]));
        fit_params[0].append(fit_vals[0])
        mean_index = [1, 4, 7]
        sigma_index = [2, 5, 8]
    
    # Four Gauss
    if b_four_peak:
        fit_vals = curve_fit(fourGauss, binRan[:-1], hist_pixels[cap_idx], guess_array[1], method='dogbox', max_nfev=fit_max_eval);
        fit_pixels[1].append(fourGauss(binRan[:-1], *fit_vals[0]));
        fit_params[1].append(fit_vals[0])
        mean_index = [1, 4, 7, 10]
        sigma_index = [2, 5, 8, 11]
        
    # Five Gauss
    if b_five_peak:
        fit_vals = curve_fit(fiveGauss, binRan[:-1], hist_pixels[cap_idx], guess_array[2], method='dogbox', max_nfev=fit_max_eval)
        fit_pixels[2].append(fiveGauss(binRan[:-1], *fit_vals[0]))
        fit_params[2].append(fit_vals[0])
        mean_index = [ 1, 4, 7, 10, 13]
        sigma_index = [ 2, 5, 8, 11, 14]
        
#  #   print("Cap {} Fit Centers:".format(cap_idx))                   
#     #print(fit_vals[0])
#     # Two Gauss
#     print("{}, {}".format(fit_vals[0][1], fit_vals[0][4]))

#     # Three Gauss
#     # print("{}, {}, {}".format(fit_vals[0][1], fit_vals[0][4], fit_vals[0][7]))

#     # Four Gauss
#     # print("{}, {}, {}, {}".format(fit_vals[0][1], fit_vals[0][4], fit_vals[0][7], fit_vals[0][10]))

# Do the plotting


if test_mode:
    NUM_FIT_FUNC = 3            # Three fits
    cap_idx = CAP_LIMIT - 1     # Point to index 0
    fig,axs = plt.subplots(NUM_FIT_FUNC, 1)
    if NUM_FIT_FUNC == 1:
        axs = [axs]             # Turn into list for subscripting
    for fit_idx in range(NUM_FIT_FUNC):
        axs[fit_idx].hist(clipped_pixels[cap_idx], bins=binRan)
        axs[fit_idx].plot(binRan[:-1], fit_pixels[fit_idx][cap_idx], 'r--');
    plt.savefig('peak_test.png')
    plt.show()
        
else:
    fig,axs = plt.subplots(num_caps,1)
    
    # Special case if only one cap
    if num_caps == 1:
        axs = [axs]                 # Turn into a list so it can be subscripted

    peak_idx = num_peaks - 3;   # Analysis starts at 3 peaks, so subtract for index
    for cap_idx in range(num_caps):
        axs[cap_idx].hist(clipped_pixels[cap_idx], bins=binRan);
        axs[cap_idx].plot(binRan[:-1], fit_pixels[peak_idx][cap_idx], 'r--');
    plt.savefig('peak_fit.png')
    plt.show()

#print("Fit values")
#print(fit_vals)
#print("Histogram range")
#print(binRan)
#print("Clipped pixels[0]")
#print(clipped_pixels[0])
#print("Clipped pixels full")
#print(clipped_pixels)
#print("Fit pixels")
#print(fit_pixels)

if analysis_mode:
    peak_sel = num_peaks - 3;   # Starts at 3 peaks
    for cap_idx in range(num_caps):
        print("Cap {} Parameters".format(cap_idx))
        mu_string = "Mu".rjust(8)
        sigma_string = "Sigma".rjust(8)
        for peak_idx in range(num_peaks):
            #print(peak_sel,cap_idx,mean_index,[sigma_idx],peak_idx)
            #print(fit_params[peak_sel][cap_idx])
            mu = fit_params[peak_sel][cap_idx][mean_index[peak_idx]]
            sigma = math.fabs(fit_params[peak_sel][cap_idx][sigma_index[peak_idx]])
            mu_string += "{:11.3e}  ".format(mu)
            sigma_string += "{:11.3e}  ".format(sigma)

        print(mu_string)
        print(sigma_string)

# Pickle the results
pickleFile = open('result_fullrange.pickle', 'wb')
pickle.dump(fit_params, pickleFile)
pickleFile.close()

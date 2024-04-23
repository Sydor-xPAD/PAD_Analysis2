import os
import numpy as np
import matplotlib.pyplot as plt
import Big_keck_load as BKL
import math
import pickle
import sys
import configparser
from scipy.optimize import curve_fit
import scipy
import glob

class lse_min:
    def __init__(self):
        self.x_data = [];
        self.y_data = [];
        self.min_func = None

    def do_lse(self, x_vals):
        
        calc_y = self.min_func(self.x_data, *x_vals)
        total_err = 0
        for y_idx in range(len(self.y_data)):
            total_err = total_err + (calc_y[y_idx]-self.y_data[y_idx])**2;
        return total_err

def do_lse_real(x_vals, args):
    min_obj = args;
    return min_obj.do_lse(x_vals);
    
    
cfg_parser = configparser.ConfigParser()
cfg_parser.read("bipartite.ini")

fit_max_eval = int(cfg_parser['Analysis']['fit_max_eval'])
bgFilename = cfg_parser['Analysis']['bg_image_filename']
fgFilename = cfg_parser['Analysis']['fg_image_filename']
image_width = int(cfg_parser['Default']['img_width'])
image_height = int(cfg_parser['Default']['img_height'])
num_caps = int(cfg_parser['Default']['num_caps'])
file_offset = int(cfg_parser['Default']['file_offset'])
file_gap = int(cfg_parser['Default']['file_gap'])
sensor_bpp = int(cfg_parser['Default']['bpp'])
asic_width = int(cfg_parser['Default']['asic_width'])
asic_height = int(cfg_parser['Default']['asic_height'])
asic_start_x = int(cfg_parser['Analysis']['asic_start_x'])
asic_start_y = int(cfg_parser['Analysis']['asic_start_y'])

sys_type = cfg_parser['Default']['sys_type']
if sys_type == 'keckpad':
    load_func = BKL.keckFrame
elif sys_type == 'mmpad':
    load_func = BKL.mmpadFrame
else:
    print("Unrecognized system type: " + sys_type)
    sys.exit(1)

trim_pixels = int(cfg_parser['Analysis']['trim_pixels'])

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

def twoClipQuad(xdata, a, b, c, d, e, f, g):
    global fit_invoke
    fit_invoke += 1
    result_y = np.arange(xdata.size).astype(np.double);
    for x_idx in range(xdata.size):
        x = xdata[x_idx];
        #quad_one = ((a*x)+b)*x+c;
        #quad_two = ((d*x)+e)*x+f;
        quad_one = a*(x-b)**2+c;
        quad_two = d*(x-e)**2+f;
        
        result_y[x_idx] = np.max([quad_one, quad_two]);
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
    
backImageData = open(bgFilename,"rb")

backStack = np.zeros((num_caps,image_height,image_width),dtype=np.double)
numImages = int(os.path.getsize(bgFilename)/(file_gap+image_height*image_width*sensor_bpp/8))

#Calc cap backs
for fIdex in range(numImages):
   payload = load_func(backImageData)
   backStack[(payload[3]-1)%num_caps,:,:] += np.resize(payload[4],[image_height,image_width])
backStack = backStack/ (numImages/num_caps)

# Iterate over all foreground images
fgImageFile = open(fgFilename, "rb");
numFgImages = int(os.path.getsize(fgFilename)/(file_gap+image_height*image_width*sensor_bpp/8));
fgStack = np.zeros((num_caps,image_height,image_width),dtype=np.double)

print("There are {} foreground images.".format(numFgImages))

for fIdx in range(numFgImages):
    payload = load_func(fgImageFile);
    #if (fIdx < 4):
    #    continue
    curr_frame = payload[4].reshape([image_height,image_width]);
    fmbImg = curr_frame - backStack[(payload[3]-1)%num_caps,:,:];

    curr_asic = fmbImg[asic_start_y:(asic_start_y+asic_height),asic_start_x:(asic_start_x+asic_width)] # Just get the ASIC of interest

    num_asic_pixels = asic_width * asic_height; # Base pixels in an ASIC
    curr_slice = curr_asic.reshape([num_asic_pixels])
    curr_slice.sort()           # Sort to get the pixels ready for quartiles
    stripped_slice = curr_slice[trim_pixels:(num_asic_pixels-1-trim_pixels)]
    num_stripped_pixels = len(stripped_slice)

    low_avg = stripped_slice[int(num_stripped_pixels/8)] # Middle of first quartile
    high_avg = stripped_slice[int(num_stripped_pixels*7/8)] # Middle of fourth quartile

    binRan = np.arange(math.floor(stripped_slice[0]), math.ceil(stripped_slice[-1])) # Cover the whole spread

    strip_hist = np.histogram(stripped_slice, bins=binRan[:-1])[0]
    # First peak Amplitude, mean, std; Second peak Amplitute, mean, std; offset
    guess_val = [ strip_hist.max(), low_avg, 10, strip_hist.max(), high_avg, 10, 0]

    min_2g = lse_min()
    min_2g.x_data = binRan
    min_2g.y_data = strip_hist
    min_2g.min_func = twoGauss;

    res = scipy.optimize.minimize(do_lse_real, np.array(guess_val), args=min_2g, method="Nelder-Mead",options={"adaptive":True})
    fit_vals = res.x

    fit_pixels = twoGauss(binRan[:-1], *fit_vals)

    print("Means: {}\t{}".format(fit_vals[1],fit_vals[4]))


    # First peak Amplitude, mean, std; Second peak Amplitute, mean, std; Third peak Amplitude, mean, std; offset
    guess_val = [ strip_hist.max(), low_avg, 10, strip_hist.max(), (low_avg+high_avg)/2, 10, strip_hist.max(), high_avg, 10, 0]
    #guess_val = [ strip_hist.max(), low_avg, 10, strip_hist.max(), 300, 10, strip_hist.max(), 500, 10, 0]

    guess_val = [-0.1, 0, 300, -0.1, 70, 50, 0]

    min_3g = lse_min()
    min_3g.x_data = binRan
    min_3g.y_data = strip_hist
    min_3g.min_func = twoClipQuad;

    #res = scipy.optimize.minimize(do_lse_real, np.array(guess_val), args=min_3g, method="Nelder-Mead",options={"adaptive":True})
    #fit_vals3 = res.x

    #fit_pixels3 = twoClipQuad(binRan[:-1], *fit_vals3)

    
    fig,ax = plt.subplots(1,1)

    ax.hist(stripped_slice, bins=binRan)
    ax.plot(binRan[:-1], fit_pixels, 'r--')
    #ax.plot(binRan[:-1], fit_pixels3, 'v--')
    plt.show()
                           
        # Close the file
fgImageFile.close();

sys.exit(1)

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
    guess_val = [1, 0, 10, 0.9, 50, 10, 0.5, 100, 10, 0]
    guess_val[0] = np.max(hist_pixels)
    guess_val[3] = guess_val[0]*0.9
    guess_val[6] = guess_val[0]*0.5;
    
    guess_array[0] = guess_val

    #     # Four Gauss
    guess_val = [1, 0, 10, 0.9, 100, 10, 0.5, 200, 10, 0.2, 300, 10, 0]
    guess_val[0] = np.max(hist_pixels)
    guess_val[3] = guess_val[0]*0.9
    guess_val[6] = guess_val[0]*0.5
    guess_val[9] = guess_val[0]*0.5;

    guess_array[1] = guess_val

    #     # Five Gauss
    guess_val = [1, 0, 10, 0.9, 100, 10, 0.5, 200, 10, 0.2, 300, 10, 0.1, 400, 10, 0]
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
        min3g = lse_min();
        min3g.x_data = binRan[:-1];
        min3g.y_data = hist_pixels[cap_idx];
        min3g.min_func = threeGauss;
        
        res = scipy.optimize.minimize(do_lse_real, np.array(guess_array[0]), args=min3g, method="Nelder-Mead",options={"adaptive":True});
        
        fit_vals = res.x
        print(res.x)
        fit_pixels[0].append(threeGauss(binRan[:-1], *fit_vals));
        fit_params[0].append(fit_vals)
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

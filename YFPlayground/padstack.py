import Big_keck_load as BKL
import numpy as np
import scipy
import math
import multiprocessing
import threading
import time

class PADSM:
    SM_BASE_WIDTH = 256
    SM_BASE_HEIGHT = 128
    SM_EXP_WIDTH = 259          # Expanded width
    SM_EXP_HEIGHT = 128         # Expanded height

def quadratic(x, a, b, c):
    return x*x*a+x*b+c

def vertex_pos(a, b, c):
    if a >= 0:
        return 0                # Vertex does not face correct direction

    center = -b/(2*a);          # The roots are spaced evenly around -b/(2a), so don't need discriminant
    return center

    
    
def bilinear_interp(img, src_y, src_x):
    jy = int(math.floor(src_y))
    jx = int(math.floor(src_x))
    dy = src_y - jy
    dx = src_x - jx

    yx = [0,0]
    base_yx0 = img[jy, jx]
    base_yx1 = img[jy+1, jx]
    #yx[0] = (img[jy, jx+1]-img[jy,jx])*dx + img[jy,jx]
    #yx[1] = (img[jy+1, jx+1]-img[jy+1,jx])*dx+img[jy+1,jx]
    yx[0] = (img[jy, jx+1]-base_yx0)*dx + base_yx0
    yx[1] = (img[jy+1, jx+1]-base_yx1)*dx+base_yx1
    return (yx[1]-yx[0])*dy+yx[0]
    
                             
    
def parse_gc_params(gc_filename):
    gc_file = open(gc_filename, 'r')
    gc_list = []
    # XXX Assumes lines in order
    for line in gc_file:
        split_line = line.split(',')
        theta = float(split_line[3].strip())/180*math.pi
        min_x = float(split_line[4].strip())
        min_y = float(split_line[5].strip())
        gc_list.append((theta, min_x, min_y))

    gc_file.close()
    return gc_list

def split_sm(img, sm_size):
    img_size = img.shape;
    #print(img_size, sm_size)
    if img_size[0] % sm_size[0] != 0 or \
       img_size[1] % sm_size[1] != 0:
        return [];           # Invalid size

    num_sm_row = img_size[0]//sm_size[0]
    num_sm_col = img_size[1]//sm_size[1]

    sm_list = []
    sm_idx = -1

    for row_idx in range(num_sm_row):
        start_row = row_idx*sm_size[0]
        end_row = start_row+sm_size[0]
        for col_idx in range(num_sm_col):
            start_col = col_idx*sm_size[1]
            end_col = start_col+sm_size[1]
            sm_idx = sm_idx+1
            curr_sm = img[start_row:end_row,start_col:end_col]
            sm_append = curr_sm[:] # Make sure we copy the data
            sm_list.append(sm_append)

    return sm_list
            
def sm_expand(sm_img):
    
    out_sm = np.ndarray((128, 259), dtype=np.float64)*0
    out_sm[:,0:128] = sm_img[:,0:128] # Copy the left half
    out_sm[:,(128+3):259] = sm_img[:,128:256] # Copy the right half
    out_sm[:,127] = sm_img[:,127]*0.4
    out_sm[:,128] = sm_img[:,127]*0.4
    out_sm[:,129] = sm_img[:,127]*0.2+sm_img[:,128]*0.2
    out_sm[:,130] = sm_img[:,128]*0.4
    out_sm[:,131] = sm_img[:,128]*0.4
    return out_sm

class PADStack:
    SP_TYPE_NONE = 0;
    SP_TYPE_BG = 1;
    SP_TYPE_FF = 2;             # We may have special types for some operations
    SP_TYPE_DEFECT = 3;
    
    def __init__(self, oldPADStack):
        self.numImages = oldPADStack.numImages;
        self.capMask = oldPADStack.capMask
        self.capIndex = oldPADStack.capIndex[:]
        self.imgStack = oldPADStack.imgStack[:]
        self.metaStack = oldPADStack.metaStack[:]
        self.numCaps = oldPADStack.numCaps
        self.spType = oldPADStack.sp_type
        self.imgSize = oldPADStack.imgSize
        self.dtype = oldPADStack.dtype
        
    def __init__(self, xpad_file, xpad_type, file_type = 'IMG'):
        self.numImages = 0
        self.capMask = 0
        self.capIndex = []
        self.imgStack = []
        self.metaStack = []
        self.numCaps = 0
        self.spType = self.SP_TYPE_NONE # Start as a basic stack
        self.histBinStart = -200
        self.histBinEnd = 800
        self.numBins = 200
        self.fpHeight = 50
        self.fpWidth = (3,30)

        # Set the limits of debouncing
        if xpad_type == "KECK" or xpad_type == "KECKPADX2":
            self.fpBound=(-50,50)
        else:
            self.fpBound=(-150,150)

        if (file_type == 'IMG'):
            self.loadImg(xpad_file, xpad_type)
        elif (file_type == 'FF'):
            self.loadFF(xpad_file, xpad_type)
        elif (file_type == 'DEFECT'):
            self.loadDefect(xpad_file, xpad_type)
        
        
    def calcMaskDetails(self):
        # Given the cap mask, compute the index map and num caps
        tempMask = (self.capMask >> 1) # remove the dummy bit
        currIdx = 0
        while(tempMask != 0):
            if (tempMask & 0x1) != 0:
                self.numCaps += 1
                self.capIndex.append(currIdx)
            tempMask = tempMask >> 1
            currIdx += 1

        return

    def computeBgStack(self, frame_skip = 2):
        self.spType = self.SP_TYPE_BG
        numCaps = self.numCaps

        # Create the output stack
        outStack = []
        for stackIdx in range(numCaps):
            new_array = np.zeros(self.imgSize)
            outStack.append(new_array)

        # I know how many frames there are, so I can start at the right number
        framesToSkip = numCaps*frame_skip
        if self.numImages > framesToSkip:
            startFrame = framesToSkip
        else:
            startFrame = 0      # Don't skip frames if we don't have enough

        # Now we can start the summation
        for frameIdx in range(startFrame, self.numImages):
            outStack[frameIdx % numCaps] += self.imgStack[frameIdx].reshape(self.imgSize)

        # Average out the frames
        num_avg = (self.numImages-startFrame)//numCaps
        for capIdx in range(numCaps):
            outStack[capIdx] = outStack[capIdx]/num_avg

        self.imgStack = outStack
        self.numImages = numCaps

    def bgSub(self, bgImg):
        # Check the cap masks to see if they match
        if (self.capMask != bgImg.capMask) or (bgImg.spType != self.SP_TYPE_BG):
            print("Cap masks do not match.")
            return False

        # For now, assume the sizes match
        numFrames = self.numImages

        for frameIdx in range(numFrames):
            #print("bgsub frameIdx: {}".format(frameIdx))
            #print(self.imgSize)
            #print(self.imgStack[frameIdx].shape)
            #print(bgImg.imgStack[frameIdx % self.numCaps].shape)
            self.imgStack[frameIdx] = self.imgStack[frameIdx].reshape((self.imgSize[0],self.imgSize[1])) - bgImg.imgStack[frameIdx % self.numCaps]

        return True

    def loadFF(self, xpad_file, imgType):
        if imgType == 'KECK':
            self.numImages = 8
            self.imgSize = (512,512)
            self.numCaps = 8
            self.capMask = 0x1ff
        elif imgType == 'MMPAD':
            self.numImages = 1
            self.imgSize = (512,512)
            self.numCaps = 1
            self.capMask = 0x1
        elif imgType == 'KECKPADX2':
            self.numImages = 8
            self.imgSize = (512,1024)
            self.numCaps = 8
            self.capMask = 0x1ff
        else:
            return              # Not a supported type

        ff_file = open(xpad_file, 'rb')
        self.imgStack = []
        for cap_idx in range(self.numCaps):
            curr_frame = np.fromfile(ff_file, dtype=np.double, count=(self.imgSize[0]*self.imgSize[1]))
            curr_frame = curr_frame.reshape(self.imgSize)
            self.imgStack.append(curr_frame)
        ff_file.close()
        self.spType = self.SP_TYPE_FF
        return

    def applyFF(self, ffImg):
        if ffImg.spType != self.SP_TYPE_FF:
            return              # Wrong type
        num_caps = self.numCaps
        num_img = self.numImages

        for frame_idx in range(num_img):
            cap_num = frame_idx % num_caps
            self.imgStack[frame_idx] = self.imgStack[frame_idx]*ffImg.imgStack[self.capIndex[cap_num]]

        return
        
                
    def loadImg(self, xpad_file, imgType):
        # Get the details from the image file
        kf = BKL.KeckFrame(xpad_file, imgType)
        bOpen = kf.open()

        if not bOpen:
            return

        self.numImages = kf.numImages

        for img_idx in range(self.numImages):
            currMeta, currFrame = kf.getFrame();
            self.metaStack.append(currMeta)
            self.imgStack.append(currFrame);

            # If the first frame, we have to extract some
            # metadata and compute a few values
            if (img_idx == 0):
                self.capMask = (self.metaStack[0].frameMeta[6]>>12) & 0x1ff
                if self.capMask == 0: # Not technically valid, but OK for MMPAD
                    self.capMask = 0x003 # One cap, cap 1
                    
                self.calcMaskDetails();

        self.imgSize = (self.metaStack[0].lengthParms[2], self.metaStack[0].lengthParms[1])
        self.dtype = kf.dtype
        kf.close()
        
    def apply_debounce(self):
        self.debounce_log = []; # Clear the debounce log
        ASIC_WIDTH = 128
        ASIC_HEIGHT = 128
        ASIC_MARGIN = 4

        asic_x_count = self.imgSize[1]//ASIC_WIDTH
        asic_y_count = self.imgSize[0]//ASIC_WIDTH
        numImages = self.numImages
        debounce_amount = 0
        debounce_reason = ""
        debounce_msg = ""
        
        
        for frame_idx in range(numImages):
            curr_frame = self.imgStack[frame_idx]
            for x_idx in range(asic_x_count):
                asic_x_min = x_idx*ASIC_WIDTH
                asic_x_max = asic_x_min + ASIC_WIDTH-1
                x_min = x_idx*ASIC_WIDTH + ASIC_MARGIN
                x_max = x_min+ASIC_WIDTH - ASIC_MARGIN-ASIC_MARGIN
                for y_idx in range(asic_y_count):
                    asic_y_min = y_idx*ASIC_HEIGHT
                    asic_y_max = asic_y_min + ASIC_HEIGHT-1
                    y_min = y_idx*ASIC_HEIGHT + ASIC_MARGIN
                    y_max = y_min+ASIC_HEIGHT - ASIC_MARGIN - ASIC_MARGIN
                    curr_asic = curr_frame[y_min:y_max,x_min:x_max]
                    asic_idx = y_idx*asic_x_count+x_idx;
                    
                    # First, compute a histogram of the pixels
                    curr_hist,bin_edge = np.histogram(curr_asic, bins=self.numBins, range=(self.histBinStart, self.histBinEnd))

                    
                    peak_ret = scipy.signal.find_peaks(curr_hist, height=self.fpHeight, width=self.fpWidth);
                    curr_peaks = peak_ret[0]

                    if (frame_idx == 3) and (y_idx==1):
                        hist_filename = "histogram_x{}.txt".format(x_idx)
                        hist_file = open(hist_filename, "w")

                        for hist_pop in curr_hist:
                            hist_file.write(str(hist_pop))
                            hist_file.write(",")
                        hist_file.write("\n")

                        for hist_edge in bin_edge:
                            hist_file.write(str(hist_edge))
                            hist_file.write(",")
                        hist_file.write("\n")
                        hist_file.close()
                        

                    #print(len(curr_peaks))
                    ENABLE_QUADRATIC = 1;
                    if (len(curr_peaks)>=2):
                        zero_peak = 0.5*(bin_edge[curr_peaks[0]]+bin_edge[curr_peaks[0]+1])
                        debounce_msg = ""
                        if (zero_peak >= self.fpBound[0]) and (zero_peak <= self.fpBound[1]):
                            curr_frame[asic_y_min:asic_y_max,asic_x_min:asic_x_max] = curr_frame[asic_y_min:asic_y_max,asic_x_min:asic_x_max] - zero_peak
                            debounce_amount = zero_peak
                            debounce_reason = "Applied Topo"
                        else:
                            debounce_amount = zero_peak
                            debounce_reason = "Topo out of range"
                    elif (len(curr_peaks)==1):
                        peak_width, width_heights, left_ips, right_ips = scipy.signal.peak_widths(curr_hist, curr_peaks);
                        #print(peak_width)
                        left_idx = math.floor(left_ips[0])
                        right_idx = math.ceil(right_ips[0])
                        
                        x_centers = 0.5 *(bin_edge[left_idx:right_idx]+bin_edge[(left_idx+1):(right_idx+1)]);
                        ##print(x_centers)
                        quad_fit_ret = scipy.optimize.curve_fit(quadratic, x_centers, curr_hist[left_idx:right_idx], [-1,20,400])
                        quad_coeff = quad_fit_ret[0]
                        debounce_msg = quad_coeff
                        #print(quad_fit_ret)
                        zero_peak = vertex_pos(*quad_coeff);
                        debounce_amount = zero_peak
                        if (zero_peak >= self.fpBound[0]) and (zero_peak <= self.fpBound[1]):
                            curr_frame[asic_y_min:asic_y_max,asic_x_min:asic_x_max] = curr_frame[asic_y_min:asic_y_max,asic_x_min:asic_x_max] - zero_peak
                            debounce_reason = "Adaptive quadratic"
                        else:
                            debounce_reason = "Adaptive quadratic out of range"
                    else:
                        debounce_amount = 0
                        debounce_reason = "No peaks found"
                        deboucne_msg = ""
                    self.debounce_log.append([frame_idx, asic_idx, debounce_amount, debounce_reason, debounce_msg])        

    def applyDefect(self, defectImg):
        if defectImg.spType != self.SP_TYPE_DEFECT:
            print("Invalid defect map.")
            return

        num_caps = self.numCaps
        num_img = self.numImages

        for frame_idx in range(num_img):
            cap_num = frame_idx % num_caps
            self.imgStack[frame_idx] = self.imgStack[frame_idx]+defectImg.imgStack[self.capIndex[cap_num]]

        return
                            
    def loadDefect(self, xpad_file, imgType):
        
        if imgType == 'KECK':
            self.numImages = 8
            self.imgSize = (512,512)
            self.numCaps = 8
            self.capMask = 0x1ff
        elif imgType == 'MMPAD':
            self.numImages = 1
            self.imgSize = (512,512)
            self.numCaps = 1
            self.capMask = 0x1
        elif imgType == 'KECKPADX2':
            self.numImages = 8
            self.imgSize = (512,1024)
            self.numCaps = 8
            self.capMask = 0x1ff
        else:
            print("Error: invalid type {} creating defect map.".format(imgType))
            
            return              # Not a supported type

        self.spType = self.SP_TYPE_DEFECT
        
        defect_hot_name  = xpad_file+"hot_pixels.pgm"
        defect_dark_name = xpad_file+"dark_pixels.pgm"

        defect_names = [defect_hot_name, defect_dark_name]

        # Create the array for the mask
        self.imgStack = []
        for capIdx in range(self.numCaps):
            curr_frame = np.zeros(self.imgSize, dtype=np.double) # Doubles let us NaN, which allows for adding the defect map to an image
            self.imgStack.append(curr_frame)

        # Now to load in the files
        for mask_name in defect_names:
            print("Defect map: {}".format(mask_name))
            mask_file = open(mask_name, 'r') # Need to read in names via text files
            first_line = mask_file.readline() # This is the header
            second_line = mask_file.readline() # This is the mandatory comment line
            third_line = mask_file.readline()  # This is the size line
            fourth_line = mask_file.readline() # This is the maxval line, with one newline at the end
            header_end = mask_file.tell()
            mask_file.close();              # Done with reading header
            mask_file = open(mask_name, 'rb') # Now open in binary mode
            mask_file.seek(header_end, 0)     # Skip the header

            # Now we can read in the raster
            for capIdx in range(self.numCaps):
                curr_mask = np.fromfile(mask_file, dtype=np.uint8, count=self.imgSize[0]*self.imgSize[1]).reshape(self.imgSize)
                for row_idx in range(self.imgSize[0]):
                    for col_idx in range(self.imgSize[1]):
                        if curr_mask[row_idx,col_idx] != 0:
                            self.imgStack[capIdx][row_idx,col_idx] += np.nan # Make it NaN for use later
                

    def nan_pad(self):
        num_slices = len(self.imgStack)
        if num_slices == 0:
            return              # Nothing to do
        img_size = self.imgStack[0].shape
        new_size = (img_size[0]+2, img_size[1]+2)
        img_type = self.imgStack[0].dtype
        new_img_stack = []
        for slice_idx in range(num_slices):
            curr_slice = np.ndarray(shape=new_size, dtype=img_type)
            curr_slice = curr_slice+np.nan
            curr_slice[1:(img_size[0]+1),1:(img_size[1]+1)]=self.imgStack[slice_idx][:]
            new_img_stack.append(curr_slice)

        self.imgStack = new_img_stack
        return

    def nan_filter(self, b_restore_size=True):
        num_slices = len(self.imgStack)
        if num_slices == 0:
            return
        pad_img_size = self.imgStack[0].shape
        base_img_size = (pad_img_size[0]-2, pad_img_size[1]-2)
        for slice_idx in range(num_slices):
            curr_slice = self.imgStack[slice_idx][:] # Need a copy for iterative replacement
            for y_idx in range(1, base_img_size[1]+1):
                for x_idx in range(1, base_img_size[0]+1):
                    if np.isnan(curr_slice[y_idx,x_idx]):
                        curr_slice[y_idx,x_idx] = np.nanmedian(self.imgStack[slice_idx][(y_idx-1):(y_idx+2),(x_idx-1):(x_idx+2)])

            if b_restore_size:            
                self.imgStack[slice_idx] = curr_slice[1:(base_img_size[0]+1),1:(base_img_size[1]+1)]
            else:
                self.imgStack[slice_idx] = curr_slice
            
        return

    def compute_loc_matrix(self, in_sm, gc_params):
        sm = sm_expand(in_sm)   # Compute on ultimate submodule
        
        src_size = sm.shape
        dest_size = self.calc_rot_size(sm, gc_params[0])
        src_offset = (src_size[0]/2.0, src_size[1]/2.0)
        dest_offset = (dest_size[0]/2.0, dest_size[1]/2.0)
        theta = gc_params[0]
        x_frac = gc_params[1]-math.floor(gc_params[1])
        y_frac = gc_params[2]-math.floor(gc_params[2])

        x_array = np.ndarray(dest_size, dtype=np.float64) # Matrix holding source x location
        y_array = np.ndarray(dest_size, dtype=np.float64) # Matrix holding source y location
        for y_idx in range(dest_size[0]):
            for x_idx in range(dest_size[1]):
                src_x = math.cos(theta)*(x_idx-dest_offset[1]) + math.sin(theta)*(y_idx-dest_offset[0])+src_offset[1] - x_frac
                src_y = -math.sin(theta)*(x_idx-dest_offset[1]) + math.cos(theta)*(y_idx-dest_offset[0]) + src_offset[0] - y_frac
                x_array[y_idx,x_idx] = src_x
                y_array[y_idx,x_idx] = src_y


        return (y_array, x_array)

    def rotate_sm_ctrl(self, rotate_args):
        return self.rotate_sm_preloc(*rotate_args)
    
    def rotate_sm_preloc(self, sm, gc_params, loc_matrix):
        y_loc = loc_matrix[0]
        x_loc = loc_matrix[1]   # Extract the locations 
        src_size = sm.shape
        dest_size = y_loc.shape # We have already calculated the output size
        src_offset = (src_size[0]/2.0, src_size[1]/2.0)
        dest_offset = (dest_size[0]/2.0, dest_size[1]/2.0)
        theta = gc_params[0]
        x_frac = gc_params[1]-math.floor(gc_params[1])
        y_frac = gc_params[2]-math.floor(gc_params[2])
        
        dest_array = np.ndarray(dest_size, dtype=np.float64)
        total_interp_time = 0
        for y_idx in range(dest_size[0]):
            for x_idx in range(dest_size[1]):
                src_x = x_loc[y_idx,x_idx]
                src_y = y_loc[y_idx,x_idx] # Retrieve the pre-computed indices

                # Check in bounds
                if src_x >= 0 and src_x < (src_size[1]-1) and \
                   src_y >= 0 and src_y < (src_size[0]-1):
                    interp_start_time = time.time()
                    dest_array[y_idx,x_idx] = bilinear_interp(sm, src_y, src_x)
                    interp_stop_time =time.time()
                    total_interp_time += (interp_stop_time - interp_start_time)
                else:
                    dest_array[y_idx,x_idx] = np.nan

        print("Interpolation proper: {}".format(total_interp_time))
        return (dest_array, ((dest_size[0]-src_size[0])/2.0, (dest_size[1]-src_size[1])/2.0))
                    
    
    def rotate_sm(self, sm, gc_params):
        src_size = sm.shape
        dest_size = self.calc_rot_size(sm, gc_params[0])
        src_offset = (src_size[0]/2.0, src_size[1]/2.0)
        dest_offset = (dest_size[0]/2.0, dest_size[1]/2.0)
        theta = gc_params[0]
        x_frac = gc_params[1]-math.floor(gc_params[1])
        y_frac = gc_params[2]-math.floor(gc_params[2])

        dest_array = np.ndarray(dest_size, dtype=np.float64)
        for y_idx in range(dest_size[0]):
            for x_idx in range(dest_size[1]):
                src_x = math.cos(theta)*(x_idx-dest_offset[1]) + math.sin(theta)*(y_idx-dest_offset[0])+src_offset[1] - x_frac
                src_y = -math.sin(theta)*(x_idx-dest_offset[1]) + math.cos(theta)*(y_idx-dest_offset[0]) + src_offset[0] - y_frac

                                
                # Check pixel in bounds
                if src_x >= 0 and src_x < (src_size[1]-1) and \
                   src_y >= 0 and src_y < (src_size[0]-1):
                    dest_array[y_idx,x_idx] = bilinear_interp(sm, src_y, src_x)
                else:
                    dest_array[y_idx,x_idx] = np.nan

        return (dest_array, ((dest_size[0]-src_size[0])/2.0, (dest_size[1]-src_size[1])/2.0))

    def rotate_thread_ninterp(self, base_sm, gc_params, curr_loc, pixel_loc, base_points, out_sm_list, out_offset_list, sm_idx):
        out_sm = sm_expand(base_sm)
        line_sm = out_sm.reshape((-1,1))
        
        dest_size = curr_loc[0].shape
        src_size = out_sm.shape

        y = np.arange(128)
        x = np.arange(259)
        start_time = time.time()
        #interp = scipy.interpolate.LinearNDInterpolator(base_points, line_sm)
        #z = interp(pixel_loc)
        z = scipy.interpolate.interpn((y,x), out_sm, pixel_loc, bounds_error=False)
        end_time = time.time()
        print("Interpolation proper took: {}".format(end_time-start_time))
        ordered = z.reshape(dest_size, order='C')
        dest_offset = ((dest_size[0]-src_size[0])/2.0, (dest_size[1]-src_size[1])/2.0)
        out_sm_list[sm_idx] = ordered
        out_offset_list[sm_idx] = dest_offset
        
    
    def rotate_thread_ctrl(self, base_sm, gc_params, pixel_loc, out_sm_list, out_offset_list, sm_idx):
        #print("Submodule index: {}".format(sm_idx))
        start_time = time.time()
        out_sm = sm_expand(base_sm)
        expand_time = time.time()
        dest_array, dest_offset = self.rotate_sm_preloc(out_sm+0, gc_params, pixel_loc)
        end_time = time.time()
        print("Thread {} expansion {}, rotation {}".format(sm_idx, expand_time-start_time, end_time-expand_time))
        out_sm_list[sm_idx] = dest_array
        #print("Thread control: {}".format(dest_offset))
        out_offset_list[sm_idx] = dest_offset
        end_time = time.time()
        print("Thread {} took {}.".format(sm_idx,end_time-start_time))
        return
    
    def calc_rot_size(self, img, theta):
        img_size = img.shape

        max_x = 0
        max_y = 0
        min_x = 0
        min_y = 0

        vertex_array = [(0,0), (img_size[0],0), (0, img_size[1]), (img_size[0], img_size[1])]

        for vertex in vertex_array:
            new_x = vertex[1]*math.cos(theta)-vertex[0]*math.sin(theta)
            new_y = vertex[1]*math.sin(theta)+vertex[0]*math.cos(theta)

            if (new_x > max_x):
                max_x = new_x
            if (new_x < min_x):
                min_x = new_x
            if (new_y > max_y):
                max_y = new_y
            if (new_y < min_y):
                min_y = new_y

        dest_height = math.floor(max_y - min_y)
        dest_width = math.floor(max_x - min_x)

        if (dest_height - img_size[0]) % 2 == 1:
            dest_height = dest_height+ 1
        if (dest_width - img_size[1]) % 2 == 1:
            dest_width = dest_width + 1

        return (dest_height, dest_width)
    
    def geocorr(self, gc_params_filename=None):
        full_size=(612, 532)    # Size of a full normal camera frame after geocal
        sm_size = (128, 256)

        gc_params = parse_gc_params(gc_params_filename)

        print(gc_params)
        num_slices = len(self.imgStack)
        if num_slices == 0:
            return

        print("Geocorr: {} slices".format(num_slices))
        pad_img_size = self.imgStack[0].shape

        out_stack = []

        ## Compute the parameters for the geocorr
        matrix_loc_list = []
        sm_idx = -1
        sm_list = split_sm(self.imgStack[0], sm_size)
        for sm in sm_list:
            sm_idx = sm_idx+1
            matrix_loc = self.compute_loc_matrix(sm, gc_params[sm_idx])
            matrix_loc_list.append(matrix_loc)
            
        
        for slice_idx in range(num_slices):
            out_slice = np.ndarray(full_size, dtype=np.float64)+np.nan # We always have to allocate a new slice; maybe the plus NaN will be faster than times NaN
            
            curr_slice = self.imgStack[slice_idx] # Need a copy for iterative replacement
            
            sm_list = split_sm(self.imgStack[slice_idx], sm_size)

                
            sm_idx = -1
            for sm in sm_list:
                sm_idx = sm_idx + 1
                curr_params = gc_params[sm_idx]
                out_sm = sm_expand(sm)

                ##rotated_sm, offset = self.rotate_sm(out_sm, curr_params)
                rotated_sm, offset = self.rotate_sm_preloc(out_sm, curr_params, matrix_loc_list[sm_idx])
                #print(rotated_sm.shape)
                top_left_x = int(math.floor(curr_params[1]-offset[1]))
                top_left_y = int(math.floor(curr_params[2]-offset[0]))
                out_slice[top_left_y:(top_left_y+rotated_sm.shape[0]),top_left_x:(top_left_x+rotated_sm.shape[1])] = rotated_sm
            #out_stack.append(out_slice) # Try making a new list
            self.imgStack[slice_idx] = out_slice
        #self.imgStack= out_stack;
                
                
            
        return

    def geocorr_truethread(self, gc_params_filename=None):
        full_size=(612, 532)    # Size of a full normal camera frame after geocal
        sm_size = (128, 256)

        gc_params = parse_gc_params(gc_params_filename)

        print(gc_params)
        num_slices = len(self.imgStack)
        if num_slices == 0:
            return

        print("Geocorr: {} slices".format(num_slices))
        pad_img_size = self.imgStack[0].shape

        out_stack = []

        ## Compute the parameters for the geocorr
        matrix_loc_list = []
        full_loc_list = []
        sm_idx = -1
        sm_list = split_sm(self.imgStack[0], sm_size)
        for sm in sm_list:
            sm_idx = sm_idx+1
            matrix_loc = self.compute_loc_matrix(sm, gc_params[sm_idx])
            y_locs = matrix_loc[0].reshape((-1,1))
            x_locs = matrix_loc[1].reshape((-1,1))
            num_locs = y_locs.shape[0]
            full_loc = np.ndarray((num_locs, 2), dtype=np.float64)
            for loc_idx in range(num_locs):
                full_loc[loc_idx, 0] = y_locs[loc_idx,0]
                full_loc[loc_idx, 1] = x_locs[loc_idx,0]
            matrix_loc_list.append(matrix_loc)
            full_loc_list.append(full_loc)
        x_src_pos = np.arange(259)
        y_src_pos = np.arange(128)
        base_x, base_y = np.meshgrid(x_src_pos, y_src_pos)
        base_x = base_x.reshape(-1)
        base_y = base_y.reshape(-1)
        base_points = np.ndarray((base_x.shape[0],2))
        base_points[:,0] = base_x
        base_points[:,1] = base_y
        
        for slice_idx in range(num_slices):
            start_time = time.time()
            print("Slice start: ".format(start_time))
            out_slice = np.ndarray(full_size, dtype=np.float64) # We always have to allocate a new slice
            out_slice.fill(np.nan) # initialize to NaN
            
            curr_slice = self.imgStack[slice_idx] # Need a copy for iterative replacement
            
            sm_list = split_sm(self.imgStack[slice_idx], sm_size)

            out_sm_list = [None] * len(sm_list)
            out_offset_list = [None] * len(sm_list) # Shallow copies for list of right lenbth
            curr_time = time.time()
            print("Initialize slice: {}".format(curr_time - start_time))
            rotate_params_list = []
            sm_idx = -1
            top_left_list = []
            thread_list = []
            for sm in sm_list:
                sm_idx = sm_idx + 1
                curr_params = gc_params[sm_idx]
                curr_loc = matrix_loc_list[sm_idx]
                curr_full_loc = full_loc_list[sm_idx]

                #t = threading.Thread(target=self.rotate_thread_ctrl, args=(sm, curr_params, curr_loc, out_sm_list, out_offset_list, sm_idx))
                t = threading.Thread(target=self.rotate_thread_ninterp, args=(sm, curr_params, curr_loc, curr_full_loc, base_points, out_sm_list, out_offset_list, sm_idx))
                thread_list.append(t)

                top_left_list.append((curr_params[2],curr_params[1]))

            curr_time = time.time()
            print("Threads created: {}".format(curr_time - start_time))
            for t in thread_list:
                t.start()

            curr_time = time.time()
            print("Threads started: {}".format(curr_time - start_time))
                
            for t in thread_list:
                t.join()

            curr_time = time.time()
            print("Threads joined: {}".format(curr_time - start_time))
            
            num_sm = len(sm_list)
            for sm_idx in range(num_sm):
                curr_out_sm = out_sm_list[sm_idx]
                curr_offset = out_offset_list[sm_idx]
                #print("Top left list:")
                #print(top_left_list[sm_idx])
                #print("Offset:")
                #print(curr_offset)
                #print("Len offset list:{}".format(len(out_offset_list)))
                #print("Shape(offset_item):{}".format(out_offset_list[0].shape))
                top_left_x = int(math.floor(top_left_list[sm_idx][1]-curr_offset[1]))
                top_left_y = int(math.floor(top_left_list[sm_idx][0]-curr_offset[0]))
                out_slice[top_left_y:(top_left_y+curr_out_sm.shape[0]),top_left_x:(top_left_x+curr_out_sm.shape[1])] = curr_out_sm
            self.imgStack[slice_idx] = out_slice
            curr_time = time.time()
            print("Slice assembled and copied: {}".format(curr_time - start_time))

    def geocorr_thread(self, gc_params_filename=None):
        full_size=(612, 532)    # Size of a full normal camera frame after geocal
        sm_size = (128, 256)

        gc_params = parse_gc_params(gc_params_filename)

        print(gc_params)
        num_slices = len(self.imgStack)
        if num_slices == 0:
            return

        print("Geocorr: {} slices".format(num_slices))
        pad_img_size = self.imgStack[0].shape

        out_stack = []

        ## Compute the parameters for the geocorr
        matrix_loc_list = []
        sm_idx = -1
        sm_list = split_sm(self.imgStack[0], sm_size)
        for sm in sm_list:
            sm_idx = sm_idx+1
            matrix_loc = self.compute_loc_matrix(sm, gc_params[sm_idx])
            matrix_loc_list.append(matrix_loc)
            
        
        for slice_idx in range(num_slices):
            out_slice = np.ndarray(full_size, dtype=np.float64)+np.nan # We always have to allocate a new slice; maybe the plus NaN will be faster than times NaN
            
            curr_slice = self.imgStack[slice_idx] # Need a copy for iterative replacement
            
            sm_list = split_sm(self.imgStack[slice_idx], sm_size)

            rotate_params_list = []
            sm_idx = -1
            for sm in sm_list:
                sm_idx = sm_idx + 1
                rotate_params_list.append((sm, gc_params[sm_idx], matrix_loc_list[sm_idx]))

            with multiprocessing.Pool(8) as p:
                out_results = p.map(self.rotate_sm_ctrl, rotate_params_list)
                
            sm_idx = -1
            for sm in out_results:
                sm_idx = sm_idx + 1
                curr_params = gc_params[sm_idx]

                rotated_sm = out_results[sm_idx][0]
                offset = out_results[sm_idx][1]
                
                top_left_x = int(math.floor(curr_params[1]-offset[1]))
                top_left_y = int(math.floor(curr_params[2]-offset[0]))
                out_slice[top_left_y:(top_left_y+rotated_sm.shape[0]),top_left_x:(top_left_x+rotated_sm.shape[1])] = rotated_sm
            #out_stack.append(out_slice) # Try making a new list
            self.imgStack[slice_idx] = out_slice
        #self.imgStack= out_stack;
                
                
            
        return

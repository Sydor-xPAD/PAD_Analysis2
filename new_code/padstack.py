import xPadParser as BKL
import numpy as np
import scipy
import math
import multiprocessing
import threading
import time
import h5py
import math
import imageio

class GaussFit2Readnoise:
    def __init__(self):
        self.readnoise = 10
        
    def computeGaussian(self, x, sigma, mu):
        g_var = sigma*sigma     # Gaussian variance
        result = 1/(np.sqrt(2*math.pi*g_var))*np.exp(-np.pow(x-mu,2.0)/(2*g_var))
        return result
    def computeDist(self, x, scale_readnoise, mean_readnoise, scale2, mean2, sigma2, dc):
        readnoise_var = self.readnoise*self.readnoise # Sigma Squared
        peak_2_var = sigma2*sigma2

        gauss_readnoise = scale_readnoise * self.computeGaussian(x, self.readnoise, mean_readnoise)
        gauss_2 = scale2*self.computeGaussian(x, peak_2_var, mean2)
        return (gauss_readnoise+gauss_2+dc)
        
class GaussFit2:
    def __init__(self):
        self.readnoise = 10
        
    def computeGaussian(self, x, sigma, mu):
        g_var = sigma*sigma     # Gaussian variance
        result = 1/(np.sqrt(2*math.pi*g_var))*np.exp(-np.pow(x-mu,2.0)/(2*g_var))
        return result
    def computeDist(self, x, scale_readnoise, sigma_readnoise, mean_readnoise, scale2, sigma2, mean2, dc):
        readnoise_var = sigma_readnoise*sigma_readnoise # Sigma Squared
        peak_2_var = sigma2*sigma2

        gauss_readnoise = math.fabs(scale_readnoise) * self.computeGaussian(x, sigma_readnoise, mean_readnoise)
        gauss_2 = math.fabs(scale2)*self.computeGaussian(x, sigma2, mean2)
        return (gauss_readnoise+gauss_2+dc)
        

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

def split_sm_kega(img, sm_size):
    img_size = img.shape;
    #print(img_size, sm_size)
    if img_size[0] % sm_size[0] != 0 or \
       img_size[1] % sm_size[1] != 0:
        return [];           # Invalid size

    num_sm_row = img_size[0]//sm_size[0]
    num_sm_col = img_size[1]//sm_size[1]

    sm_list = []
    sm_idx = -1

    if (num_sm_row * num_sm_col) != 16:
        return []               # Invalid size


    #Submodules for KegaPAD are arranged as
    # 0    1    8    9
    # 2    3    10   11
    # 4    5    12   13
    # 6    7    14   15
    for row_idx in range(num_sm_row):
        start_row = row_idx*sm_size[0]
        end_row = start_row+sm_size[0]
        for col_idx in range(2):
            start_col = col_idx*sm_size[1]
            end_col = start_col+sm_size[1]
            sm_idx = sm_idx+1
            curr_sm = img[start_row:end_row, start_col:end_col]
            sm_append = curr_sm[:] # Make sure we copy the data
            sm_list.append(sm_append)

    for row_idx in range(num_sm_row):
        start_row = row_idx*sm_size[0]
        end_row = start_row+sm_size[0]
        for col_idx in range(2):
            start_col = col_idx*sm_size[1]+512
            end_col = start_col+sm_size[1]+512
            sm_idx = sm_idx+1
            curr_sm = img[start_row:end_row, start_col:end_col]
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

def calc_bin_num(x, data_range, num_bins):
    frac = (x-data_range[0])/(data_range[1]-data_range[0])
    bin_num = num_bins*frac
    if frac >= 1:
        bin_num = num_bins - 1

    if (bin_num >= num_bins):
        print("Bin Num Debugging.")
        print(bin_num)
        print("frac: {}".format(frac))
        print("Range: {}".format(data_range))
        print("x: {}".format(x))
    return bin_num

def angle_in_bounds(angle, bounds):
    if (bounds[0] < bounds[1]):
        if (angle >= bounds[0]) and (angle <= bounds[1]):
            return True
        else:
            return False
    if (bounds[1] > bounds[0]):
        if (angle >= bounds[0]) or (angle <= bounds[1]):
            return True
        else:
            return False
    return False

def radial_intensity(img, center, num_bins, abounds = (0, 2*math.pi)):
    r_max = -math.inf
    r_min = math.inf

    
    for y_idx in range(img.shape[0]):
        y_ctr = y_idx + 0.5
        for x_idx in range(img.shape[1]):
            x_ctr = x_idx + 0.5
            curr_angle = math.atan2(y_ctr-center[0],x_ctr-center[1])+math.pi
            if not angle_in_bounds(curr_angle, abounds):
                continue
            curr_dist = math.sqrt((x_ctr-center[1])**2+(y_ctr-center[0])**2)
            if curr_dist < r_min:
                r_min = curr_dist
            if curr_dist > r_max:
                r_max = curr_dist

    r_min = math.floor(r_min)
    r_max = math.ceil(r_max)

    if r_min == r_max:
        print("Radius out of range.")
        return None

    bin_edges = np.linspace(r_min, r_max, num_bins+1)
    total_signal = np.zeros(num_bins)
    num_counts = np.zeros(num_bins)
    
    for y_idx in range(img.shape[0]):
        y_ctr = y_idx + 0.5
        for x_idx in range(img.shape[1]):
            x_ctr = x_idx + 0.5
            curr_angle = math.atan2(-(y_ctr-center[0]),x_ctr-center[1])
            if curr_angle < 0:
                curr_angle += 2*math.pi
            if not angle_in_bounds(curr_angle, abounds):
                continue
            if not math.isfinite(img[y_idx, x_idx]):
                continue
            curr_dist = math.sqrt((x_ctr-center[1])**2+(y_ctr-center[0])**2)
            dest_bin = int(calc_bin_num(curr_dist, (r_min, r_max), num_bins))
            total_signal[dest_bin] += img[y_idx, x_idx]
            num_counts[dest_bin] += 1


    return (bin_edges, total_signal, num_counts)

    
    

class PADStack:
    SP_TYPE_NONE = 0;
    SP_TYPE_BG = 1;
    SP_TYPE_FF = 2;             # We may have special types for some operations
    SP_TYPE_DEFECT = 3;
    SP_TYPE_SINGLEMASK = 4;
    
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
            self.debounce_log = []
        elif (file_type == 'FF'):
            self.loadFF(xpad_file, xpad_type)
        elif (file_type == 'DEFECT'):
            self.loadDefect(xpad_file, xpad_type)
        elif (file_type == 'SINGLEMASK'):
            self.loadSingleMask(xpad_file, xpad_type)
        elif (file_type == 'HDF'):
            self.loadHDF(xpad_file)
        
        
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

    def loadHDF(self, filename):
        with h5py.File(filename, 'r') as f:
            # Load the image raster
            if 'image' in f['/']:
                dset = f['/image']
                img_shape = dset.shape
                if len(img_shape) != 3:
                    raise ValueError("Image of wrong shape")
                num_img = img_shape[0]
                for img_idx in range(num_img):
                    curr_img = dset[img_idx,:,:]
                    self.imgStack.append(curr_img)

                self.imgSize = self.imgStack[0].shape
                self.numImages = num_img
            if 'operation_log' in f['/']:
                self.op_log = []
                dset = f['/operation_log']
                for op in dset:
                    self.op_log.append(op)

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

        self.op_log.append("Applied background subtraction")
            
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

        self.op_log.append("Applied flatfield")
        
        for frame_idx in range(num_img):
            cap_num = frame_idx % num_caps
            self.imgStack[frame_idx] = self.imgStack[frame_idx]*ffImg.imgStack[self.capIndex[cap_num]]

        return

    def saveImg(self, out_filename):
        with h5py.File(out_filename, 'w') as f:
            num_img = len(self.imgStack)
            if num_img > 0:
                img_size = self.imgStack[0].shape
                dset = f.create_dataset("image", (num_img, img_size[0], img_size[1]), dtype=np.double)
                for img_idx in range(num_img):
                    dset[img_idx,:,:] = self.imgStack[img_idx]
                if len(self.debounce_log) > 0:
                    num_asic = 16 #-=-= XXX This must be changed for KegaPAD
                    db_amt_dset = f.create_dataset("debounce_amount", (num_img, num_asic), dtype=np.double)
                    db_msg_dset = f.create_dataset("debounce_msg", (num_img, num_asic), dtype=h5py.string_dtype())
                    for db in self.debounce_log:
                        img_idx = db[0]
                        asic_idx = db[1]
                        db_amt = db[2]
                        db_msg = db[3]
                        db_amt_dset[img_idx,asic_idx] = db_amt
                        db_msg_dset[img_idx,asic_idx] = db_msg

                if len(self.op_log) > 0:
                    op_dset = f.create_dataset("operation_log", (len(self.op_log),), dtype=h5py.string_dtype())
                    for op_idx in range(len(self.op_log)):
                        op_dset[op_idx] = self.op_log[op_idx]

                f['/image'].attrs['cap_mask'] = self.capMask
                integ_dset = f.create_dataset("integration_time", (num_img,), dtype=np.float64)
                inter_dset = f.create_dataset("interframe_time", (num_img,), dtype=np.float64)
                capnum_dset = f.create_dataset("cap_num", (num_img,), dtype='i')
                v_iss_buf_pix_dset = f.create_dataset("v_iss_buf_pix", (num_img, len(self.metaStack[0].v_iss_buf_pix)), dtype=np.float64)
                v_iss_ab_dset = f.create_dataset("v_iss_ab", (num_img, len(self.metaStack[0].v_iss_ab)), dtype=np.float64)
                v_mon_out_dset = f.create_dataset("v_mon_out", (num_img, len(self.metaStack[0].v_mon_out)), dtype=np.float64)
                v_iss_buf_dset = f.create_dataset("v_iss_buf", (num_img, len(self.metaStack[0].v_iss_buf)), dtype=np.float64)
                vdda_current_dset = f.create_dataset("vdda_current", (num_img, len(self.metaStack[0].vdda_current)), dtype=np.float64)
                vdda_volts_dset = f.create_dataset("vdda_volts", (num_img, len(self.metaStack[0].vdda_volts)), dtype=np.float64)
                sensor_temp_dset = f.create_dataset("sensor_temp", (num_img, len(self.metaStack[0].sensorTemp)), dtype=np.float64)
                for img_idx in range(num_img):
                    integ_dset[img_idx] = self.metaStack[img_idx].integTime
                    inter_dset[img_idx] = self.metaStack[img_idx].interTime
                    capnum_dset[img_idx] = self.metaStack[img_idx].capNum
                    v_iss_buf_pix_dset[img_idx] = self.metaStack[img_idx].v_iss_buf_pix
                    v_iss_ab_dset[img_idx] = self.metaStack[img_idx].v_iss_ab
                    v_mon_out_dset[img_idx] = self.metaStack[img_idx].v_mon_out
                    v_iss_buf_dset[img_idx] = self.metaStack[img_idx].v_iss_buf
                    vdda_current_dset[img_idx] = self.metaStack[img_idx].vdda_current
                    vdda_volts_dset[img_idx] = self.metaStack[img_idx].vdda_volts
                    sensor_temp_dset[img_idx] = self.metaStack[img_idx].sensorTemp
                    
        return

    def saveImgKega(self, out_filename):
        with h5py.File(out_filename, 'w') as f:
            num_img = len(self.imgStack)
            if num_img > 0:
                img_size = self.imgStack[0].shape
                dset = f.create_dataset("image", (num_img, img_size[0], img_size[1]), dtype=np.double)
                for img_idx in range(num_img):
                    dset[img_idx,:,:] = self.imgStack[img_idx]
                if len(self.debounce_log) > 0:
                    num_asic = 32 #-=-= XXX This must be changed for KegaPAD
                    db_amt_dset = f.create_dataset("debounce_amount", (num_img, num_asic), dtype=np.double)
                    db_msg_dset = f.create_dataset("debounce_msg", (num_img, num_asic), dtype=h5py.string_dtype())
                    for db in self.debounce_log:
                        img_idx = db[0]
                        asic_idx = db[1]
                        db_amt = db[2]
                        db_msg = db[3]
                        db_amt_dset[img_idx,asic_idx] = db_amt
                        db_msg_dset[img_idx,asic_idx] = db_msg

                if len(self.op_log) > 0:
                    op_dset = f.create_dataset("operation_log", (len(self.op_log),), dtype=h5py.string_dtype())
                    for op_idx in range(len(self.op_log)):
                        op_dset[op_idx] = self.op_log[op_idx]

                f['/image'].attrs['cap_mask'] = self.capMask
                integ_dset = f.create_dataset("integration_time", (num_img,), dtype=np.float64)
                inter_dset = f.create_dataset("interframe_time", (num_img,), dtype=np.float64)
                capnum_dset = f.create_dataset("cap_num", (num_img,), dtype='i')
                v_iss_buf_pix_dset = f.create_dataset("v_iss_buf_pix", (num_img, len(self.metaStack[0].v_iss_buf_pix)), dtype=np.float64)
                v_iss_ab_dset = f.create_dataset("v_iss_ab", (num_img, len(self.metaStack[0].v_iss_ab)), dtype=np.float64)
                v_mon_out_dset = f.create_dataset("v_mon_out", (num_img, len(self.metaStack[0].v_mon_out)), dtype=np.float64)
                v_iss_buf_dset = f.create_dataset("v_iss_buf", (num_img, len(self.metaStack[0].v_iss_buf)), dtype=np.float64)
                vdda_current_dset = f.create_dataset("vdda_current", (num_img, len(self.metaStack[0].vdda_current)), dtype=np.float64)
                vdda_volts_dset = f.create_dataset("vdda_volts", (num_img, len(self.metaStack[0].vdda_volts)), dtype=np.float64)
                sensor_temp_dset = f.create_dataset("sensor_temp", (num_img, len(self.metaStack[0].sensorTemp)), dtype=np.float64)
                for img_idx in range(num_img):
                    integ_dset[img_idx] = self.metaStack[img_idx].integTime
                    inter_dset[img_idx] = self.metaStack[img_idx].interTime
                    capnum_dset[img_idx] = self.metaStack[img_idx].capNum
                    v_iss_buf_pix_dset[img_idx] = self.metaStack[img_idx].v_iss_buf_pix
                    v_iss_ab_dset[img_idx] = self.metaStack[img_idx].v_iss_ab
                    v_mon_out_dset[img_idx] = self.metaStack[img_idx].v_mon_out
                    v_iss_buf_dset[img_idx] = self.metaStack[img_idx].v_iss_buf
                    vdda_current_dset[img_idx] = self.metaStack[img_idx].vdda_current
                    vdda_volts_dset[img_idx] = self.metaStack[img_idx].vdda_volts
                    sensor_temp_dset[img_idx] = self.metaStack[img_idx].sensorTemp
                    
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
        for frame_idx in range(len(self.imgStack)):
            self.imgStack[frame_idx] = self.imgStack[frame_idx].reshape((self.imgSize[0],self.imgSize[1]))
            
        self.dtype = kf.dtype
        kf.close()
        self.op_log = []        # Start with a blank log of recorded operations
        
    def apply_debounce(self, MaskFilename = None):
        self.debounce_log = []; # Clear the debounce log
        self.asic_stats = []
        self.asic_details = []
        ASIC_WIDTH = 128
        ASIC_HEIGHT = 128
        ASIC_MARGIN = 4

        asic_x_count = self.imgSize[1]//ASIC_WIDTH
        asic_y_count = self.imgSize[0]//ASIC_WIDTH
        numImages = self.numImages
        debounce_amount = 0
        debounce_reason = ""
        debounce_msg = ""

        self.op_log.append("Applied debounce")

        use_maskfile = True
        mask_image = np.ndarray((self.imgSize[0], self.imgSize[1]))
        if MaskFilename is None:
            use_maskfile = False
        else:
            mask_image = imageio.imread(MaskFilename)
            
        for frame_idx in range(numImages):
            curr_frame = self.imgStack[frame_idx]
            ADJUST_RANGE = 0
            if ADJUST_RANGE != 0:
                sample_region = curr_frame[208:240,401:494].flatten()
                adj_factor = np.nanmedian(sample_region)
                print("Frame adjustment factor is {}".format(adj_factor))
                curr_frame = curr_frame - adj_factor
                sample_region = curr_frame[208:240,401:494].flatten()
                adj_factor = np.nanmedian(sample_region)
                print("After adjustment, new value is: {}".format(adj_factor))
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

                    full_asic = curr_frame[asic_y_min:asic_y_max, asic_x_min:asic_x_max]

                    mask_asic = mask_image[asic_y_min:asic_y_max,asic_x_min:asic_x_max]
                    # Get some statistics on the ASIC
                    
                    in_range_array = np.where(np.logical_and(np.greater_equal(curr_asic, self.histBinStart),np.less_equal(curr_asic,self.histBinEnd)), curr_asic, [np.nan]).flatten()
                    self.asic_stats.append([frame_idx, asic_idx, np.nanmean(in_range_array), np.nanmedian(in_range_array)])
                    
                    # First, compute a histogram of the pixels
                    curr_hist,bin_edge = np.histogram(curr_asic, bins=self.numBins, range=(self.histBinStart, self.histBinEnd))

                    self.asic_details.append([frame_idx, asic_idx, curr_hist, bin_edge])
                    
                    peak_ret = scipy.signal.find_peaks(curr_hist, height=self.fpHeight, width=self.fpWidth);
                    curr_peaks = peak_ret[0]

                    FRAME_DIAGNOSTICS = 0
                    if FRAME_DIAGNOSTICS != 0:
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
                        

                    # If a mask is defined, we use the mask as the determinant of bounce amound
                    if use_maskfile:
                        sel_pixels = np.extract(np.not_equal(0, mask_asic), full_asic)
                        debounce_amount = np.nanmedian(sel_pixels)
                        curr_frame[asic_y_min:asic_y_max,asic_x_min:asic_x_max] = curr_frame[asic_y_min:asic_y_max,asic_x_min:asic_x_max] - debounce_amount
                        debounce_reason = "Masked selection"
                    else:
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
                            #print(curr_peaks)
                            x_centers = 0.5 *(bin_edge[left_idx:right_idx]+bin_edge[(left_idx+1):(right_idx+1)]);
                            ##print(x_centers)
                            quad_fit_ret = scipy.optimize.curve_fit(quadratic, x_centers, curr_hist[left_idx:right_idx], [-1,20,400])
                            quad_coeff = quad_fit_ret[0]
                            debounce_msg = quad_coeff
                            #print(quad_fit_ret)
                            zero_peak = vertex_pos(*quad_coeff);
                            debounce_amount = zero_peak
                            ## XXX FIXME OVERRIDE
                            #if (asic_idx == 11):
                            #    print("Raw peak amount: {}".format(zero_peak))
                            #debounce_amount = 0
                            #zero_peak = 0

                            # Time to try fitting two peaks under certain conditions
                            COMPUTE_TWOPEAK = 1 # Eventually put make an intelligent decision
                            if COMPUTE_TWOPEAK:
                                raw_data = np.concatenate([np.full((count,),midpoint) for count, midpoint in zip(curr_hist, 0.5*(bin_edge[0:-1]+bin_edge[1:]))])
                                asic_skew = scipy.stats.skew(raw_data)
                                #print("Skew: {}".format(asic_skew))
                                if True or asic_skew > 0.45:
                                
                                    fitter = GaussFit2()
                                    peak_height = curr_hist[curr_peaks[0]]
                                    readnoise = 14.0
                                    peak_scale = peak_height*math.sqrt(2*math.pi*readnoise**2)
                                    #initial_guess = [curr_hist[curr_peaks[0]], 14.0, zero_peak, curr_hist[curr_peaks[0]], 14.0, zero_peak+60, 0]
                                    initial_guess = [peak_scale, readnoise, zero_peak, peak_scale/2.0, readnoise, zero_peak+40, 0]
                                    print("ASIC: {}".format(asic_idx))
                                    print(initial_guess)
                                    fit_found = True
                                    try:
                                        print("Trying two-peak fit.")
                                        two_fit_ret = scipy.optimize.curve_fit(fitter.computeDist, 0.5*(bin_edge[0:-1]+bin_edge[1:]), curr_hist, initial_guess, method='dogbox')
                                    except Exception as e:
                                        fit_found = False # Assume the error is failing to converge
                                    
                                    print("Old Zero Peak: {}".format(zero_peak))
                                    if fit_found:
                                        peak_1 = two_fit_ret[0][2]
                                        peak_2 = two_fit_ret[0][5]
                                        temp_peak = peak_1
                                        if peak_1 < peak_2:
                                            temp_peak = peak_1
                                        else:
                                            temp_peak = peak_2

                                        # Make sure the new peak is roughly in range
                                        ## Below 15 could be a function of photon energy
                                        if math.fabs(temp_peak-zero_peak) < 15:
                                            zero_peak = temp_peak
                                        
                                            
                                        print("New Zero Peak: {}".format(zero_peak))
                                    
                            #print(zero_peak)
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
            self.imgStack[frame_idx] = curr_frame
            
    def applyDefect(self, defectImg):
        if defectImg.spType != self.SP_TYPE_DEFECT:
            print("Invalid defect map.")
            return

        num_caps = self.numCaps
        num_img = self.numImages

        self.op_log.append("Applied defect map.")
        
        for frame_idx in range(num_img):
            cap_num = frame_idx % num_caps
            self.imgStack[frame_idx] = self.imgStack[frame_idx]+defectImg.imgStack[self.capIndex[cap_num]]

        return

    def loadSingleMask(self, mask_file, imgType):
        if imgType == 'KECK':
            self.numImages = 1
            self.imgSize = (512,512)
        elif imgType == 'MMPAD':
            self.numImages = 1
            self.imgSize = (512,512)
        elif imgType == 'KECKPADX2':
            self.imgSize = (512,1024)
            self.numImages = 1
        else:
            print("Error: invalid type {} creating defect map.".format(imgType))
            
            return              # Not a supported type

        temp_raster = imageio.imread(mask_file)
        if temp_raster.shape != self.imgSize:
            print("Error: invalid mask size {}; should be {}.".format(temp_raster.shape, self.imgSize))
            return

        # Create the array for the mask
        self.imgStack = []
        curr_frame = np.zeros(self.imgSize, dtype=np.double) # Doubles let us NaN, which allows for adding the defect map to an image
        self.imgStack.append(curr_frame)

        for row_idx in range(self.imgSize[0]):
            for col_idx in range(self.imgSize[1]):
                if temp_raster[row_idx,col_idx] != 0:
                    self.imgStack[0][row_idx,col_idx] += np.nan # Make it NaN for use later

        self.spType = self.SP_TYPE_SINGLEMASK
        return

    def augmentMask(self, singlemaskImg):
        if singlemaskImg.spType != self.SP_TYPE_SINGLEMASK:
            print("Invalid single-mask image.")
            return

        for imgIdx in range(self.numImages):
            self.imgStack[imgIdx] = self.imgStack[imgIdx] + singlemaskImg.imgStack[0] # The mask images are either 0 or NaN, thereby either not changing pixels or masking them out

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
        z = scipy.interpolate.interpn((y,x), out_sm, pixel_loc, bounds_error=False)
        ordered = z.reshape(dest_size, order='C')
        dest_offset = ((dest_size[0]-src_size[0])/2.0, (dest_size[1]-src_size[1])/2.0)
        out_sm_list[sm_idx] = ordered
        out_offset_list[sm_idx] = dest_offset
        
    
    def rotate_thread_ctrl(self, base_sm, gc_params, pixel_loc, out_sm_list, out_offset_list, sm_idx):
        #print("Submodule index: {}".format(sm_idx))
        out_sm = sm_expand(base_sm)
        dest_array, dest_offset = self.rotate_sm_preloc(out_sm+0, gc_params, pixel_loc)
        out_sm_list[sm_idx] = dest_array
        #print("Thread control: {}".format(dest_offset))
        out_offset_list[sm_idx] = dest_offset
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

        num_slices = len(self.imgStack)
        if num_slices == 0:
            return

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
            out_slice = np.ndarray(full_size, dtype=np.float64) # We always have to allocate a new slice
            out_slice.fill(np.nan) # initialize to NaN
            
            curr_slice = self.imgStack[slice_idx] # Need a copy for iterative replacement
            
            sm_list = split_sm(self.imgStack[slice_idx], sm_size)

            out_sm_list = [None] * len(sm_list)
            out_offset_list = [None] * len(sm_list) # Shallow copies for list of right lenbth
            rotate_params_list = []
            sm_idx = -1
            top_left_list = []
            thread_list = []
            for sm in sm_list:
                sm_idx = sm_idx + 1
                curr_params = gc_params[sm_idx]
                curr_loc = matrix_loc_list[sm_idx]
                curr_full_loc = full_loc_list[sm_idx]

                t = threading.Thread(target=self.rotate_thread_ninterp, args=(sm, curr_params, curr_loc, curr_full_loc, base_points, out_sm_list, out_offset_list, sm_idx))
                thread_list.append(t)

                top_left_list.append((curr_params[2],curr_params[1]))

            for t in thread_list:
                t.start()

                            
            for t in thread_list:
                t.join()

                        
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

    def geocorr_truethread_kega(self, gc_params_filename=None):
        full_size=(612, 1072)    # Size of a full normal camera frame after geocal
        sm_size = (128, 256)

        gc_params = parse_gc_params(gc_params_filename)

        num_slices = len(self.imgStack)
        if num_slices == 0:
            return

        pad_img_size = self.imgStack[0].shape

        out_stack = []

        ## Compute the parameters for the geocorr
        matrix_loc_list = []
        full_loc_list = []
        sm_idx = -1
        sm_list = split_sm_kega(self.imgStack[0], sm_size)
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
            out_slice = np.ndarray(full_size, dtype=np.float64) # We always have to allocate a new slice
            out_slice.fill(np.nan) # initialize to NaN
            
            curr_slice = self.imgStack[slice_idx] # Need a copy for iterative replacement
            
            sm_list = split_sm_kega(self.imgStack[slice_idx], sm_size)

            out_sm_list = [None] * len(sm_list)
            out_offset_list = [None] * len(sm_list) # Shallow copies for list of right lenbth
            rotate_params_list = []
            sm_idx = -1
            top_left_list = []
            thread_list = []
            for sm in sm_list:
                sm_idx = sm_idx + 1
                curr_params = gc_params[sm_idx]
                curr_loc = matrix_loc_list[sm_idx]
                curr_full_loc = full_loc_list[sm_idx]

                t = threading.Thread(target=self.rotate_thread_ninterp, args=(sm, curr_params, curr_loc, curr_full_loc, base_points, out_sm_list, out_offset_list, sm_idx))
                thread_list.append(t)

                top_left_list.append((curr_params[2],curr_params[1]))

            for t in thread_list:
                t.start()

                            
            for t in thread_list:
                t.join()

                        
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

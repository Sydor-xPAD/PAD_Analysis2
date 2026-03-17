import Big_keck_load as BKL
import numpy as np
import scipy

class PADSM:
    SM_BASE_WIDTH = 256
    SM_BASE_HEIGHT = 128
    SM_EXP_WIDTH = 259          # Expanded width
    SM_EXP_HEIGHT = 128         # Expanded height

def split_sm(img, sm_size):
    img_size = img.shape;
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
            return False

        # For now, assume the sizes match
        numFrames = self.numImages

        for frameIdx in range(numFrames):
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
        ASIC_WIDTH = 128
        ASIC_HEIGHT = 128
        ASIC_MARGIN = 4

        asic_x_count = self.imgSize[1]//ASIC_WIDTH
        asic_y_count = self.imgSize[0]//ASIC_WIDTH
        numImages = self.numImages
        
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
                    
                    # First, compute a histogram of the pixels
                    curr_hist,bin_edge = np.histogram(curr_asic, bins=self.numBins, range=(self.histBinStart, self.histBinEnd))

                    
                    peak_ret = scipy.signal.find_peaks(curr_hist, height=self.fpHeight, width=self.fpWidth);
                    curr_peaks = peak_ret[0]

                    #print(len(curr_peaks))
                    if (len(curr_peaks)>=1):
                        zero_peak = 0.5*(bin_edge[curr_peaks[0]]+bin_edge[curr_peaks[0]+1])
                        if (zero_peak >= self.fpBound[0]) and (zero_peak <= self.fpBound[1]):
                            curr_frame[asic_y_min:asic_y_max,asic_x_min:asic_x_max] = curr_frame[asic_y_min:asic_y_max,asic_x_min:asic_x_max] - zero_peak

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

    def geocorr(self, gc_params=None):
        full_size=(612, 532)    # Size of a full normal camera frame after geocal
        sm_size = (128, 256)
        
        num_slices = len(self.imgStack)
        if num_slices == 0:
            return
        
        pad_img_size = self.imgStack[0].shape
        
        for slice_idx in range(num_slices):
            out_slice = np.ndarray(full_size, dtype=np.float64)*0
            curr_slice = self.imgStack[slice_idx] # Need a copy for iterative replacement
            
            sm_list = split_sm(curr_slice, sm_size)
            sm_idx = -1
            for sm in sm_list:
                sm_idx = sm_idx + 1
                out_sm = sm_expand(sm)
                sm_col = sm_idx % 2
                sm_row = sm_idx // 2
                out_col = 261*sm_col
                out_row = 132*sm_row
                out_slice[out_row:(out_row+sm_size[0]),out_col:(out_col+sm_size[1]+3)] = out_sm
            self.imgStack[slice_idx] = out_slice
            
        return

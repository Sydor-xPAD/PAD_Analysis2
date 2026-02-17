import Big_keck_load as BKL
import numpy as np

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
        
    def __init__(self, xpad_file, xpad_type):
        self.numImages = 0
        self.capMask = 0
        self.capIndex = []
        self.imgStack = []
        self.metaStack = []
        self.numCaps = 0
        self.spType = self.SP_TYPE_NONE # Start as a basic stack

        # Get the details from the image file
        kf = BKL.KeckFrame(xpad_file, imgType = xpad_type)
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
        

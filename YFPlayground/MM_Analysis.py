#
# MMPAD Specific Analysis functions
# File: MM_Analysis.py
# History
# V 1.0 YF 1/26/24
#

import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

import numpy as np
from scipy.optimize import minimize
from scipy.stats import linregress
import pickle

global_pickle_mode = 1

def calcLinearity_MM(dobj, data=None, runnum = 0, VERBOSE = True):
    """
    data is [#run, #frame]
    runnum increments from 0 to #run-1
    NOTE - Data is stored in array data.
    stores the average value over the ROI.
    """
    PICKLE_MODE  = global_pickle_mode  # Set 0 = Do nothing. 1 = Write to file. 2 = Read from file
    


    if PICKLE_MODE == 2:
        # Load arrays from disk using pickle
        with open('ana_dig.pkl', 'rb') as file:
            data = pickle.load(file)

        # Access the arrays using the keys
        analog = data['analog']
        digital = data['digital']
        return analog,digital
    

    # Sanity checking up front
    if hasattr(dobj, "Correction_Value"):
        correctionValue = dobj.Correction_Value # expect 16384, but could be 65535 also
    else:
        raise Exception(" Correction_Value is required to be set. Make sure data was taken with 16384 (or 65535)! ")       

    back = None
    
    if hasattr(dobj, "back"):
        back = dobj.back

    fore = dobj.fore
    roi = dobj.roi
    ncaps = dobj.NCAPS

    #DEBUG  #DEBUG #DEBUG #REMOVE THIS LINE
    #fore.numImages = 200

    for fIdex in range( fore.numImages):
    
        (mdF,dataF) = fore.getFrame()
        if back:
            (mdB,dataB) = back.getFrame()
            dataF = dataF - dataB #  Put F-B in F as a kludge.

        frameNum = fIdex // ncaps  # not a typo "//" is integer division 
        dataArray = np.resize(dataF,[512,512])
        # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        
        dobj.foreStack[frameNum,:,:] = dataArray
        if VERBOSE:
            print(f"Loading {fIdex+1} / {fore.numImages} \r", end="")



    # optionaly  compute the average of just the first run, and use that as the background
    # for all subsequent runs
    if hasattr(dobj, "computeBackgroundFromFirstRun") and runnum == 0:
        ave = np.zeros( (512,512),dtype=np.double)
        for fIdex in range( fore.numImages):
            frameNum = fIdex // ncaps
            
            ave[:, :] += dobj.foreStack[frameNum,:,:]

        ave = ave /  (fore.numImages / ncaps)   
        dobj.backFromFirstRunAve = ave 
    #  [ Frame, Cap, Y , X ] 
    

    if hasattr(dobj, "backFromFirstRunAve"):
        for fIdex in range( fore.numImages):
            frameNum = fIdex // ncaps
            
            dobj.foreStack[frameNum,:,:] -=  dobj.backFromFirstRunAve[ :, :]


    # imageJ code for reference
    #var tupleA = [ val & 0x3FFF, intTime ]  // Analog and digital data MUST BE separated for this to work!
    #var tupleD = [ val >> 14, intTime ]

    analog  = np.zeros( (fore.numImages,512,512 ),dtype=np.uint16)
    digital = np.zeros( (fore.numImages,512,512),dtype=np.uint32)

    shr = int(math.log2( correctionValue)) # 16834 --> 14, 65536 --> 16.

    if 1:
        # numpy vectorized operations for speed.
        analog = np.bitwise_and(dobj.foreStack, 0x3FFF)  # Extract lower 14 bits
        digital = np.right_shift(dobj.foreStack, 14)     # Get upper bits by shifting
    
    # old code not needed.
    if 0:    
        # Crap. Handle Correction_Value = 65535. Unfortunately, I took data with CV = 65535
        # instead of 65536 so cant use a simple binary mask to separate analog and digital. they overlap
        # Require a more advanced routine to suss them apart

        
        STEPS = 100
        W = 512
        H = 512
        hist = 40000 # R bit trary

        

        

        for y in range(H):
            for x in range(W):
                previous_pv = dobj.foreStack[0,y,x]
                dig_counts = 5   # linscan3 data started at 5! Manual hand-edited fix.

                for fIdex in range( fore.numImages):
                    pv =  dobj.foreStack[fIdex,y,x]

                    if (pv-previous_pv) > hist :
                        # digital jump
                        dig_counts += 1
                    if (pv-previous_pv) < -hist :   # noisy data - 1 point jumps back down - need to handle
                        # digital jump
                        dig_counts += -1    
                    av = pv - dig_counts*correctionValue
                    analog[fIdex, y,x ] = av
                    digital[fIdex, y,x] = dig_counts
                    previous_pv = pv



                    

    if PICKLE_MODE == 1:
        # Save arrays to disk using pickle
        with open('ana_dig.pkl', 'wb') as file:
            pickle.dump({'analog': analog, 'digital': digital}, file)

    return analog, digital




"""
 analog, digital are Rank3 numpy arrays
"""

# Define the objective function (the one to minimize)
# Solve for K
def objective_function(K, analog, digital, x, y ):
    y_predicted = analog[:,y,x] + K * digital[:,y,x]
    X = range( len( y_predicted) )

    # Perform linear fit using scipy.stats.linregress
    slope, intercept, r_value, p_value, std_err = linregress(X, y_predicted)

    ##print (K, std_err) 
    return std_err*1000




"""
plot_MM
============
theData is expected to be ( analog[#Frames, Height, Width],  digital[#Frames, H, W]  )
Where each nFrame has another IR pulse in the burst count.
You must manually set PICKLE_MODE and re-run this routine.
First time, set PICKLE_MODE = 1, to save the data ( it takes a long time to run )
All subsequent times, use PICKLE_MODE = 2, to read the data from disk. 

"""
def plot_MM(theData, title, options = None):

    # Some run time options
    _Show_Analog_and_Digital_ = True # YF try
    _Find_Best_K_ = True

    PICKLE_MODE  = global_pickle_mode  # Set 0 = Do nothing. 1 = Write to file. 2 = Read from file
    


    if PICKLE_MODE == 2:
        # Load arrays from disk using pickle
        with open('bestK.pkl', 'rb') as file:
            data = pickle.load(file)

        # Access the arrays using the keys
        bestK = data['bestK']
        

        #
        #  Write bestK out as a raw file, to load into imageK for checking
        if 0:
            with open('bestK.raw', 'wb') as file:
                file.write(bestK)

            # OPEN this file with RAW format 512x512, 64bit, 0 offset, 1 image, little Endian    

        #
        #
        ### 1 ### Plot the Digital Coeffs as an image
        #
        if 1:

            plt.imshow(bestK, cmap='viridis')  # You can choose a different colormap as per your preference

            min = bestK.min()
            max = bestK.max()
            std = bestK.std()
            mean = bestK.mean()

            print(f"{min}, {max}, {mean}, {std}")
            # Set colorbar limits to match the min and max values of the data
            plt.clim(mean - 2*std, mean + 2*std)


            plt.colorbar()  # Display a colorbar for reference
            plt.show()

        # 
        ### 2 ### Create an inset ROI on each ASIC and compute the mean
        #
        if 1:
            # 4/23/25 - Revamp for Modern MMPAD - (ie #13 Airbox)
            #    [0]  [1]  [2]  [3]
            #    [4]  [5]  [6]  [7]
            #    [9]  [8]  [11] [10]
            #    [13] [12] [15] [14]
            # Notice the bottom two rows are flipped along V axis
            mean = np.zeros( (4,4), dtype = np.double)
            std = np.zeros( (4,4), dtype = np.double)
            W = 128
            H = 128
            sx_map = [  0, W, 2*W, 3*W,
                    0, W, 2*W, 3*W,
                    W, 0, 3*W, 2*W,
                    W, 0, 3*W, 2*W 
                ]
            mar = 3 # margin
            cnt  = 0
            for iy in range(4):
                for ix in range(4):
                    sx = sx_map[cnt] + mar
                    
                    sy = iy * 128 + mar
                    mean[iy,ix] = bestK[ sy : sy+128-2*mar , sx : sx+128-2*mar ].mean()
                    std[iy,ix]  = bestK[ sy : sy+128-2*mar , sx : sx+128-2*mar ].std()
                    print(f"Correction_Value[{cnt}] {round(mean[iy,ix])}")
                    cnt += 1
                     

            print("MEANS:")
            np.set_printoptions(precision=1, suppress=True)
            print(mean)
            print("STD DEVs:")
            print(std)
        return    
    


        if 0:
            # Was this code used in older configuration - perhaps for devhead?
            #    [3]  [2]  [1]  [0]
            #    [7]  [6]  [5]  [4]
            #    [11] [10] [9]  [8]
            #    [15] [14] [13] [12]
            mean = np.zeros( (4,4), dtype = np.double)
            std = np.zeros( (4,4), dtype = np.double)
            mar = 3 # margin
            for iy in range(4):
                for ix in range(4):
                    sx = (3-ix) * 128 + mar
                    sy = iy * 128 + mar
                    mean[iy,ix] = bestK[ sy : sy+128-2*mar , sx : sx+128-2*mar ].mean()
                    std[iy,ix]  = bestK[ sy : sy+128-2*mar , sx : sx+128-2*mar ].std()


            print(mean)
            print(std)


        return
        #TODO 

    
    #
    #  HERE - PICKLEMODE != 2 - continue...
    #
    analog,digital = theData
    H = analog.shape[1]
    W = analog.shape[2]
    nFrames = len(analog)
    px = 0
    py = 0

    if _Show_Analog_and_Digital_:

        # look at pixel 0,0
        fig, ax = plt.subplots()
        #plt.figure(1)

        color = 'tab:red'
        ax.set_xlabel('N pulses')
        ax.set_ylabel('Analog', color=color)
        plt.title("Analog and Digital signals")
        ax.plot(range(nFrames), analog[:,px,py], color=color)
        ax.tick_params(axis='y', labelcolor=color)

        # Create the second Y-axis
        ax2 = ax.twinx()
        color = 'tab:blue'
        ax2.set_ylabel('Digital', color=color)
        ax2.plot(range(nFrames), digital[:, px, py], color=color)
        ax2.tick_params(axis='y', labelcolor=color)

    if _Find_Best_K_:

        bestK = np.zeros( (H,W),dtype=np.double)

        #HACK step size 10 to increase speed
        #for y in range(0,H,10):
        #    for x in range(0,W,10):
        for y in range(0,H, 1):
            for x in range(0,W, 1):

                # Initial guess for K
                initial_guess = 8000

                # Set the maximum number of iterations
                max_iterations = 100

                options = {'maxiter': max_iterations}

                # Optimize to find the best K
                result = minimize(objective_function, initial_guess, args=(analog, digital, x, y), options = options)
                bestK[y,x] = result.x[0]
                print(f"{x},{y},{bestK[y,x]}\r", end = "")

        
        if PICKLE_MODE == 1:
            # Save arrays to disk using pickle
            with open('bestK.pkl', 'wb') as file:
                pickle.dump({'bestK': bestK}, file)
        

        # Plot the results - 
        if 1:    
            tx=153; ty = 41
            fig, ax = plt.subplots()
            ax.plot( range( nFrames), analog[:, ty, tx] + bestK[ty,tx] * digital[:,ty,tx] )

            ax.set_xlabel('N pulses')
            ax.set_ylabel(f"A + K*D")
            plt.title( f"Combined Plot K = {bestK[0,0]}" )


#
# 
#  data is 2 dimensions: data should be [nRuns, nFrames]
# accepts   self.fcnPlotOptions = {"xlabels": self.varList}
def prettyPlot_MM(data, title, options = None):
    nruns = len(data)
    
    fig, ax = plt.subplots()
    #plt.figure(1)
    
    # plot the average over frames versus run#
    nframes = len(data [0])
    val = np.zeros( [ nruns ])

    # skip the first frame!
    for n in range(nruns):
        val[n] = np.average(data[n,1:])
        
    xaxis = options["xlabels"]
    x = np.array(xaxis)   # convert sequence to NumPy array
    ax.plot( x, val, 'o',
                label = "Points" )


    slope, intercept = np.polyfit(x, val, 1)
    best_fit_line = slope * x + intercept

    ax.plot(x, best_fit_line, '--', label='Best fit line')



    ax.text(0.01, 0.80, f"Slope: {slope:.2f}\nIntercept: {intercept:.2f}",
        fontsize=10, color='red',
        ha='left', va='top',
        transform=ax.transAxes)

    plt.legend()
    plt.xlabel('Exposure Time')
    plt.ylabel('mean (ADU)')
    ###plt.title( title )
    ax.yaxis.set_minor_locator( MultipleLocator(1000))


def calc1_MM(dobj, data=None, runnum = 0):
    """
    data is [#run, #frame]
    runnum increments from 0 to #run-1
    NOTE - Data is stored in array data.
    stores the average value over the ROI.
    """
   
    VERBOSE = 1
    back = None
    
    if hasattr(dobj, "back"):
        back = dobj.back

    fore = dobj.fore
    roi = dobj.roi
    ncaps = 1


    for fIdex in range( fore.numImages):
        (mdF,dataF) = fore.getFrame()
        if back:
            (mdB,dataB) = back.getFrame()
            dataF = dataF - dataB #  Put F-B in F as a kludge.

        frameNum = fIdex // ncaps  # not a typo "//" is integer division 
        dataArray = np.resize(dataF,[512,512])
        # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        cnum = 0   # MMPAD fIdex % 8
        dobj.foreStack[frameNum,:,:] = dataArray
        if VERBOSE:
            print(f"Loading {fIdex} / {fore.numImages} \r", end="")



    # optionaly  compute the average of just the first run, and use that as the background
    # for all subsequent runs
    if hasattr(dobj, "computeBackgroundFromFirstRun") and runnum == 0:
        ave = np.zeros((512,512),dtype=np.double)
        for fIdex in range( fore.numImages):
            frameNum = fIdex // ncaps
            
            ave[:, :] += dobj.foreStack[frameNum,:,:]

        ave = ave /  (fore.numImages / ncaps)   
        dobj.backFromFirstRunAve = ave 
    #  [ Frame, Cap, Y , X ] 
    

    if hasattr(dobj, "backFromFirstRunAve"):
        for fIdex in range( fore.numImages):
            frameNum = fIdex // ncaps
            
            dobj.foreStack[frameNum,:,:] -=  dobj.backFromFirstRunAve[:, :]
        
    # rio is [X,Y,W,H]
    startPixY = roi[1]
    endPixY = startPixY + roi[3]
    startPixX = roi[0]
    endPixX = startPixX + roi[2]
    nImages =  fore.numImages // ncaps  # not a typo "//" is integer division 
    

    for fn in range( nImages ): 

        data[runnum, fn] = np.median( dobj.foreStack[fn,startPixY:endPixY, startPixX:endPixX] )
            #print( fn, cn, roiSum)

    return data

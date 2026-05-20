#!/usr/bin/env python3
# File: plotlineout.py
# Description - Used to Take and Analyze data on KeckPAD
# Requires an SRS box connected via Ethernet.   Varies a parameter (such as VREF_BUF) while
# sweeping the light source intensity by varying the number of pulses in BURST mode. 
# Used to map out the linearity and perhaps find the most-linear on DC biases.
#
# History
# v 0.1 6/13/23 YF - Inception
# v 0.2 6/29/23 YF - Shift to not using any bash scripts. Instead commands run directly from Python.
#
# v 0.3 7/12/23 YF Take_Data works well.
#
import numpy as np
import Big_keck_load as BKL
import os
import shutil
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import sys
import tkinter as tk
import xpad_utils as xd
from glob import glob
import pickle
from dg645 import comObject
from dg645 import DG645
import time
#
# Define some globals
#
VERBOSE = 1 # 0 = quiet, 1 = print some, 2 = print a lot

foreStack = []
backStack = []
fore = None
back = None
P = []

NRUNS = 1
RAIDPATH="/mnt/raid/keckpad"
dg = None
    
#
#
#
def takeData( params, list_commands, 
    overwrite = 1,
    runVaryCommand="", varRange = None,
    runFrameCommand = None ):
    """ 
        Run multiple Runs - issuing one command (one parameter) that changes
        at each run.
        params is a dictionary
        overWrite. Set to 1 to delete previous Runs
        list_commands = [list of string commands to send to HW ]
        runVaryCommand = string commmand
        varRange = numpy.arange( , ,) 
        
        runFrameCommand - pass in a function to call at each frame in a run
        Return dictionary of results
    """
    ####global  foreStack,backStack, fore, back
    

    # if len(params) < 8:
    #     print(" Usage: ~ setname runname FrameNum nTap zASICX zASICY ROIW ROIH")
    #     exit(0)


    setname = params["setname"]
    runname = params["runname"]
    nFrames = params["nFrames"]


    if overwrite:
        # delete old runs
        # rm -r "$RAIDPATH"/set-$setname/run-run_*
        for match in glob(f"{RAIDPATH}/set-{setname}/run-run_*"):
            shutil.rmtree(match)
            print(f"***DELETE RUN {match}")

    #
    # Create list of commands
    #  
    res = True
   
     
    
    #
    # Run through list of commands - and send them to HW
    #
    for c in list_commands:
        if VERBOSE:
            print(f"**RUN_CMD {c}")
        res = xd.run_cmd( c  )   
        if res:
            return None

    if varRange is not None:
        NRUNS = len(varRange)

    #
    # Start a series of Runs
    #
    runCount = 0
    for i in range(1, NRUNS + 1):     
        # scan a parameter here. Pass in runVaryCommand and varRange
        if runVaryCommand:
            var = varRange[0]
            varRange = varRange[1:] # remove first element
            c  = f"{runVaryCommand} {var}"
            res = xd.run_cmd(c)
            if res:
                break

        runname=f"run_{i}"        
        res = xd.run_cmd( f"startrun {runname}"  )   
        if res:
            break

        # Optionally set SRS options here and trigger SRS for each frame in the run
        # Loop <nFrames> times
        #  
        if runFrameCommand:
            for j in range(nFrames):
                runFrameCommand(j)
                time.sleep(1.0)
                
        xd.run_cmd( f"status -wait" )
        runCount += 1

    return {
        "parameters": params,
        "runCount":runCount,
        "runVaryCommand":runVaryCommand,
        "varRange":varRange
    }   

#
# not used
#
def analyzeData(aDict):
    """
    Load up the runs, and analyze
    aDict should contain "parameters", "runCount", "runVaryCommand", "varRange"
    """

    params = aDict["parameters"]
    setname = params[0]
    runname = params[1]

    foreFile = f'/mnt/raid/keckpad/set-{setname}/run-{runname}/frames/{runname}_00000001.raw' # check not sure...

    #DEBUG w local file on Windows
    foreFile = r"C:\Sydor Technologies\temptst_00000001.raw" 
    

    fore = BKL.KeckFrame( foreFile )

    backFile = f'/mnt/raid/keckpad/set-{setname}/run-back/frames/run_1_00000001.raw' 

    #DEBUG w local file on Windows
    backFile= r"C:\Sydor Technologies\temptst2_T21_00000001.raw" 

    back = BKL.KeckFrame( backFile )
    
    numImagesF = fore.numImages 
    numImagesB = back.numImages
    
    # create global big arrays to hold images
    foreStack = np.zeros((numImagesF,8,512,512),dtype=np.double)
    backStack = np.zeros((numImagesB,8,512,512),dtype=np.double)

    cap = params[2] % 8
    zSX = params[3]
    zSY = params[4]
    nTap = params[5]
    W   = params[6]
    H   = params[7]
 
    plotROI( cap, zSX, zSY, nTap, W, H )
 

 #
 #
 #

#
#
#
def plotROI(cap, zSX, zSY, nTap, W, H): 
    """ cap is cap 0-7
        zSX and zSY are 0-3 ASIC coordinate
        nTap is 1-8
        W,H are in pixels typ 128,16
    """
    global foreStack,backStack, fore, back 
    ##################################
    #Adjust for clipping
    ##################################
    clipHigh = 1e8
    clipLow = 0
    #read all the image files
    for fIdex in range( back.numImages ):
        (mdB,dataB) = back.getFrame()
        #  return frameParms, lengthParms, frameMeta, capNum, data, frameNum, integTime, interTime
        backStack[ mdB.frameNum-1,(mdB.capNum-1)%8,:,:] += np.resize(dataB,[512,512])

    avgBack = backStack/( back.numImages/8.0)

    for fIdex in range( fore.numImages):
        (mdF,dataF) = fore.getFrame()
        foreStack[mdF.frameNum-1,(mdF.capNum-1)%8,:,:] += np.resize(dataF,[512,512])

    #standDev = np.zeros((8,512,512),dtype=np.double)
    DiffStack = foreStack-backStack
    #asicSDs = np.zeros((8,16),dtype=np.double)

    #  [ Frame, Cap, Y , X ] # TODO: check Y,X is correct
    PerCapImage = DiffStack[:,cap,:,:]
    
    startPixY = zSY * 128 + (nTap-1) * 16
    endPixY = startPixY + H
    startPixX = zSX * 128
    endPixX = startPixX + W
    # frame 0 hardcoded for now
    #                       frame  ,     Y,   X  
    plt.imshow( PerCapImage[0, startPixY:endPixY, startPixX:endPixX]) # might be flipped?? #WIP#
    # TODO - we want to measure the amount of gradient, and average them over N Frames - toss out first image.
    # x axis is <varRange>  y axis is <entity> x 8 for each Cap. 
    ave_over_frames = DiffStack[ : , cap, startPixY:endPixX, startPixX:endPixX].mean(axis = 0) # Take average over rows
    data_array = ave_over_frames.mean(axis=0) # does this give me a 1-D over x?
    # Not sure ^ if thats right.

    xd.gradient_over_lineout(data_array)
    plt.show()
 
   
#
# userFunction is called for each frame of a run ( assumes an external trigger )
#
def userFunction( nLoop ):
    """ nLoop is the frame number. 
    """
    global dg
    print(f"Called userFunction n={nLoop}")
    dg.counter  = nLoop + 1
    s = f"BURC {dg.counter}" # Set the burst Count
    dg.send(s);
    dg.doTrigger()
    
#
# userFunction is called for each frame of a run ( assumes an external trigger )
#
def userFunctionB( nLoop ):
    """ nLoop is the frame number. 
    """
    global dg
    print(f"Called userFunctionB n={nLoop}")

    if strDescriptor == "Sweep_Inter1":
        del1 = nLoop * 1000 + 100
        c  = f"Interframe_nsec[1]  {del1}"  # bug?? using [0] changes them all?
    elif  strDescriptor == "Sweep_Integ1":   
        del1 = nLoop * 1000 + 100
        c  = f"Integration_nsec[1]  {del1}"  # bug?? using [0] changes them all?
    else:
        raise Exception("Error in userFunctionB. Unrecognized strDescriptor") 

    # We ARE 'allowed' to change delay param in a run (!)
    res = xd.run_cmd(c)
    dg.doTrigger()

#
#
#
def Take_Data(constStringName):
    global dg


    # Using an SRS DG645 box:
    IP_ADDR = "192.168.11.225"  
    c = comObject( 1, IP_ADDR )
    r = c.tryConnect()
    dg = DG645( c )
    dg.counter = 0 # truly python hackery
    dg.send("*CLS") # Clear errors
    
    # Future me:  dg is global, and is used in userFunction to adjust SRS box at each run frame.

    if constStringName == "Sweep_SRS_BurstCount":
        # Setup is using 1 VCSEL inside the integrating sphere. With 
        # Width Switch; the three rightmost switches (towards power connector) are down:
        # 1 1 1 1 1 0 0 0,  and there is one piece of silver mylar IFO the VCSEL 
        # Set HW parameters
        setname = 'xpad-linscan_B27'
        runname = 'varyVrefBuf'

        nFrames = 30  # frames Per Run
        # SRS is setup with PER of 100us, so 30 takes 3ms
        integrationTime = 5000000 # 5.0 millseconds
        interframeTime = 1000 # 1 usec

        # Create a dictionary of required parameters to define the run and later analysis
        parameters= {
            "setname": setname,
            "runname": runname, 
            "nFrames" : nFrames
        }




        list_commands = [
            "stop",
            "Trigger_Mode 2",
            f"Image_Count {nFrames}",
            "Cap_Select 0xF",
            f"Interframe_Nsec {interframeTime}",
            f"Integration_Nsec {integrationTime}",
            f"startset {setname}"
        ]
        # Create new Runs
        # Returns a dictionary
        takeDataRet = takeData( parameters, list_commands,
            overwrite = 1,
            runVaryCommand="DFPGA_DAC_OUT_VREF_BUF", 
            varRange = np.arange(1000,2100,200), # Expect 1000, 1200, 1400, 1600, 1800, 2000 => 6 RUNS
            runFrameCommand = userFunction )
        
        if (takeDataRet != None and takeDataRet["runCount"] > 0):
            # Pickle the results
            pickleFile = open('plo_dump.pickle', 'wb')
            pickle.dump(takeDataRet, pickleFile);
            pickleFile.close()
            return takeDataRet # return dictionary

        else:
            print(" Oh Oh. something went wrong.")
            return (0) # error   


    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    elif constStringName == "Sweep_Inter1":
        # How does the slope of dark frames change as we change the interframe1 time? 
        # Set HW parameters
        setname = 'xpad-scan_inter1_B27'
        runname = 'varyInter1' # not used :-( runs are called run1, run2...etc

        nFrames = 10  # frames Per Run  
        
        integrationTime = 100 # 100ns
        interframeTime = 100  # 100 ns - initial same on all.

        # Create a dictionary of required parameters to define the run and later analysis
        parameters= {
            "setname": setname,
            "runname": runname, 
            "nFrames" : nFrames
        }




        list_commands = [
            "stop",
            "Trigger_Mode 2",
            f"Image_Count {nFrames}",
            "Cap_Select 0x1FF",
            f"Interframe_Nsec {interframeTime}",
            f"Integration_Nsec {integrationTime}",
            f"startset {setname}"
        ]
        # Create new Runs
        # Returns a dictionary
        takeDataRet = takeData( parameters, list_commands,
            overwrite = 1,
            runVaryCommand="Readout_Delay", 
            #todo: 
            varRange = np.arange(0,150,50), # Expect 0, 50, 100, 150,  => 4 RUNS
            # NOTE that Readout_Delay is in units of 10ns clocks.
            runFrameCommand = userFunctionB )
        
        if (takeDataRet != None and takeDataRet["runCount"] > 0):
            # Pickle the results
            pickleFile = open('plo_dump.pickle', 'wb')
            pickle.dump(takeDataRet, pickleFile);
            pickleFile.close()
            return takeDataRet # return dictionary

        else:
            print(" Oh Oh. something went wrong.")
            return (0) # error   


    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    elif constStringName == "Sweep_Integ1":
        # How does the slope of dark frames change as we change the integration1 time? 
        # Set HW parameters
        setname = 'xpad-scan_integ1_B27'
        runname = '' # not used :-( runs are called run1, run2...etc

        nFrames = 10  # frames Per Run  
        
        integrationTime = 100 # 100ns
        interframeTime = 100  # 100 ns - initial same on all.

        # Create a dictionary of required parameters to define the run and later analysis
        parameters= {
            "setname": setname,
            "runname": runname, 
            "nFrames" : nFrames
        }




        list_commands = [
            "stop",
            "Trigger_Mode 2",
            f"Image_Count {nFrames}",
            "Cap_Select 0x1FF",
            f"Interframe_Nsec {interframeTime}",
            f"Integration_Nsec {integrationTime}",
            f"startset {setname}"
        ]
        # Create new Runs
        # Returns a dictionary
        takeDataRet = takeData( parameters, list_commands,
            overwrite = 1,
            runVaryCommand="Readout_Delay", 
            #todo: 
            varRange = np.arange(0,150,50), # Expect 0, 50, 100, 150,  => 4 RUNS
            # NOTE that Readout_Delay is in units of 10ns clocks.
            runFrameCommand = userFunctionB )
        
        if (takeDataRet != None and takeDataRet["runCount"] > 0):
            # Pickle the results
            pickleFile = open('plo_dump.pickle', 'wb')
            pickle.dump(takeDataRet, pickleFile);
            pickleFile.close()
            return takeDataRet # return dictionary

        else:
            print(" Oh Oh. something went wrong.")
            return (0) # error           


def Analyze_Data(constStringName):
    """
    Load up the runs, and analyze
    """
    global foreStack,backStack, fore, back 
    if constStringName == "Sweep_SRS_BurstCount":
        setname = 'xpad-linscan_B27'
        #runname = 'varyVrefBuf'
        
        roi = [46, 92, 32, 20]
        NRUNS = 6
        NCAPS = 3 # can this be pulled from file?
        runVaryCommand="DFPGA_DAC_OUT_VREF_BUF", 
        varRange = np.arange(1000,2100,200), # Make sure this matches!!
        fcnToCall = plotLinearity
        roiSumNumDims = 3
        fcnPlot = prettyPlot
 
    elif constStringName == "Sweep_Inter1":
        setname = 'xpad-scan_inter1_B27'
        #runname = 'varyVrefBuf'
        
        roi = [0, 7*16, 128, 16] # TODO - check 
        NRUNS = 3 
        NCAPS = 8 # can this be pulled from file?
        runVaryCommand="readout_delay", # this aint right. todo check. 
        varRange = np.arange(100,6100,500), # Expect 100, 600, 1100, 1600... 1000 => 10 RUNS # Make sure this matches!!
        fcnToCall = plotEachCapLineout
        roiSumNumDims = 4
        fcnPlot = prettyAllCapsInALine

    elif constStringName == "Sweep_Integ1":
        setname = 'xpad-scan_integ1_B27'
        
        roi = [0, 7*16, 128, 16] # TODO - check 
        NRUNS = 3 
        NCAPS = 8 # can this be pulled from file?
        runVaryCommand="Readout_Delay", 
        varRange = np.arange(0,1000,500), 
        fcnToCall = plotEachCapLineout
        roiSumNumDims = 4
        fcnPlot = prettyAllCapsInALine

    else:
        print("Analyze_Data(stringName), Name not valid")
        return # error out

    roiSum = None
    for runnum in range(NRUNS):
        runname = f"run_{runnum+1}"
        if 0: # Local Mac testing!
            foreFile = f'/Users/yoram/Sydor/keckpad/30KV_1.5mA_40ms_f_00015001.raw' # check not sure...
            
        else:
            foreFile = f'/mnt/raid/keckpad/set-{setname}/run-{runname}/frames/{runname}_00000001.raw' # check not sure...
        fore = BKL.KeckFrame( foreFile )

        numImagesF = fore.numImages 
        if roiSum is None:
            if roiSumNumDims == 3:
                roiSum = np.zeros((NRUNS,numImagesF // NCAPS, NCAPS),dtype=np.double)
            elif roiSumNumDims == 4:
                roiSum = np.zeros((NRUNS,numImagesF // NCAPS, NCAPS, roi[2]),dtype=np.double)


        # create global big arrays to hold images
        foreStack = np.zeros((numImagesF // NCAPS, NCAPS,512,512),dtype=np.double)
        fore.NCAPS = NCAPS # Python tom-foolery


        # Each time called, builds up data in data var/ roiSum.
        #roiSum = plotLinearity( fore, roi, data = roiSum, runnum = runnum)
        roiSum = fcnToCall( fore, roi, data = roiSum, runnum = runnum)

    if runVaryCommand:
       title = f"{runVaryCommand} {varRange}"
 
    #
    #  fcnPlot is the function to generate plot. It is defined in the IF's above.
    #
    fcnPlot (roiSum, title)
    

#
#
#
def prettyPlot(data, title):
    nruns = len(data)

    fig, ax = plt.subplots()
    #plt.figure(1)
    nframes = len(data [0])
    for n in range(nruns):
        x = .5 +.5*(n / (nruns-1))
        ax.plot( range(nframes), data[n,:,0], 
            label="Cap1" if n==0 else "", color=( x,0,0) )

    for n in range(nruns):
        x = .5 +.5*(n / (nruns-1))
        ax.plot( range(nframes), data[n,:,1], 
            label="Cap2" if n==0 else "", color = (0,0,x) )

    for n in range(nruns):
        x = .5 +.5*(n / (nruns-1))
        ax.plot( range(nframes), data[n,:,2], 
            label="Cap3" if n==0 else "", color = (0,x,0)) 


    plt.legend()
    plt.xlabel('N')
    plt.ylabel('mean (ADU)')
    plt.title( title )
    ax.yaxis.set_minor_locator( MultipleLocator(1000))
    plt.show(block=True) 

#
#   Data has <NCAPS> lineouts.  Line them all up into one lineout per image 
#
def prettyAllCapsInALine(data, title):
    """
    data should be [nRuns, nFrames, nCaps, Width_of_lineout]
    """
    nruns = len(data)

    fig, ax = plt.subplots()
    #plt.figure(1)
    nframes = len(data[0])
    ncaps = len(data[0,0] )
    dataWidth = len(data[0,0,0])

    
    for n in range(nruns):     
        for f in range(nframes):
            d = []    
            for c in range(ncaps):
                d.extend( data[n, f, c, :])
            
            x = .5 +.5*(f / (nframes-1))
            if n%3 == 0:
                clr = (x,0,0)
            elif n%3 == 1:    
                clr = (0,x,0)
            elif n%3 == 2:
                clr = (0,0,x)

            ax.plot( range(len(d)), d, color=clr,
            label=f"Run{n}" if f ==0 else "" )



    plt.legend()
    plt.xlabel('1Tap-lineout across ALL caps')
    plt.ylabel('Ave (ADU)')
    plt.title( title )
    ax.yaxis.set_minor_locator( MultipleLocator(1000))
    plt.show(block=True) 


def plotLinearity(fore, roi, data=None, runnum = 0):
    """
    fore is BKL.Keckframe
    roi is [x,y,W,H]
    title 
    data is [#run, #frame, #cap]
    runnum increments from 0 to #run-1
    NOTE - Data is NOT plotted, rather data is storted in array data.
    stores the average value over the ROI.
    """
    global foreStack,backStack
    global P
   
    ncaps = fore.NCAPS

    for fIdex in range( fore.numImages):
        (mdF,dataF) = fore.getFrame()
        frameNum = fIdex // ncaps  # not a typo "//" is integer division 
        dataArray = np.resize(dataF,[512,512])
        foreStack[frameNum,(mdF.capNum-1) % ncaps,:,:] = dataArray

    #  [ Frame, Cap, Y , X ] # TODO: check Y,X is correct
    
    # rio is [X,Y,W,H]
    startPixY = roi[1]
    endPixY = startPixY + roi[3]
    startPixX = roi[0]
    endPixX = startPixX + roi[2]
    nImages =  fore.numImages // ncaps  # not a typo "//" is integer division 
    

    for fn in range( nImages ): 
        for cn in range (ncaps):
            data[runnum, fn,cn] = np.average( foreStack[fn, cn, startPixY:endPixY, startPixX:endPixX] )
            #print( fn, cn, roiSum)

    return data


def plotEachCapLineout(fore, roi, data=None, runnum = 0):
    """
    fore is BKL.Keckframe
    roi is [x,y,W,H]
    title 
    data is [#run, #frame, #cap]
    runnum increments from 0 to #run-1
    NOTE - Data is NOT plotted, rather data is storted in array data.
    stores the average value over the ROI.
    """
    global foreStack,backStack
    global P
   
    ncaps = fore.NCAPS

    for fIdex in range( fore.numImages):
        (mdF,dataF) = fore.getFrame()
        frameNum = fIdex // ncaps  # not a typo "//" is integer division 
        dataArray = np.resize(dataF,[512,512])
        foreStack[frameNum,(mdF.capNum-1) % ncaps,:,:] = dataArray

    #  [ Frame, Cap, Y , X ] # TODO: check Y,X is correct
    
    # rio is [X,Y,W,H]
    startPixY = roi[1]
    endPixY = startPixY + roi[3]
    startPixX = roi[0]
    endPixX = startPixX + roi[2]
    nImages =  fore.numImages // ncaps  # not a typo "//" is integer division 
    

    for fn in range( nImages ): 
        for cn in range (ncaps):
            # Hopefully - axis=0 averages over columns
            data[runnum, fn,cn] = np.mean( foreStack[fn, cn, startPixY:endPixY, startPixX:endPixX], axis=0 )
            #print(f"debug:{data[runnum, fn, cn]}")

    return data



# Entry point of the script
if __name__ == "__main__":
    # Code to be executed when the script is run directly
    print("Start.")
    TAKE_DATA = 0
    LOAD_DATA = 1
    # Using SRS box - adjust burst count to get linear intensity sweeps
    #strDescriptor = "Sweep_SRS_BurstCount"
    # Adjust interframe_Time [1] - see if the gradient shapes change with delay (they dont)
    #strDescriptor = "Sweep_Inter1"
    # Adjust integration_time [1] - see if the gradient shapes change with delay
    strDescriptor = "Sweep_Integ1"

    

    
    if (TAKE_DATA):
        ret = Take_Data(strDescriptor)
        if ret == 0:
            exit(0)
        

    if (LOAD_DATA):    
        ret = Analyze_Data(strDescriptor)
        

        ####
        #pickleFile = open('plo_dump.pickle', 'rb')
        #takeDataRet =  pickle.load(pickleFile)
        #pickleFile.close()
        # Analyze the data
        #analyzeData(takeDataRet)

    print("Done!")     

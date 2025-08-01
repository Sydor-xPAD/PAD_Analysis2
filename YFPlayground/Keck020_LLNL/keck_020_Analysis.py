 #!/usr/bin/env python3
# File: keck_020_Analysis.py
# Description - Create a list of analysis routines
#
# History
# v 0.1 6/13/23 YF - Inception
# v 0.2 6/29/23 YF - Shift to not using any bash scripts. Instead commands run directly from Python.
#
# v 0.3 7/12/23 YF Take_Data works well.
# v 0.4 7/31/23 OOP the S out of it. You should be able to edit createObject() to generate
#  most data runs where one thing is varied per Run and another thing is varied per frame.
# v 0.5 8/5/23 tkinter graphics
# v 0.6 8/25/23 Allow two roi's
# v 0.7 9/18/23 Add new routines for Cornell testing

# v 0.8 9/21/23 Allow IP differences in SRS boxes in same source
# v 0.9 12/23/23 Some fixes to SMK_021 Testing
# v 2.0 5/7/25 Was plotlineout_oop - renamed to Keck_020_Analysis.py

# ***** git instructions *****
#  If weirdness you may need this - but probably not.
# git checkout HEAD -- plotlineout_oop.py   (any file name)
# Normally just this to pull over changes from the cloud
# git stash
# git fetch
# git checkout origin/yf-newcode

# Places you may need to edit this code
# Search for the word 'clipping'  where some datas are clipped fir aethetics
#  The std dev plot is one such case.

#
# INSTRUCTIONS
#

#
# Issues with mmcmd - try this:
# mmclient -s -t &
# mmcmd open 1
#

# Python bit of workaround to load modules from the parent folder
import sys
import os

# Get the parent directory and add it to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)


import numpy as np
import Big_keck_load as BKL
import os
import shutil
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import sys
#import tkinter as tk
import xpad_utils as xd
from glob import glob
import pickle
from dg645 import comObject
from dg645 import DG645
import time
#from ipywidgets import *
#from IPython.display import display
import UI_utils

import configparser


#
# Define some globals 
#
VERBOSE = 1 # 0 = quiet, 1 = print some, 2 = print a lot
#
#
# User edit settings
RAIDPATH=r"\\SYDOR-NAS01\RawDataBackup\CHESS_Nov2024\sydor_keck_data"
#\set-CornellTests_24-11-06\run-FG_CeO2_111_200_0p1ms_200ns_4"
print(RAIDPATH)
exit
#
# 
#   
 
# OOP the heck out of this
class dataObject:
    def __init__(self, strDescriptor, 
                 bTakeData=False, bAnalyzeData = False):
        self.strDescriptor = strDescriptor
        self.dg = None  # Optional Delay Generator
        self.TakeBG = False
        self.MessageBeforeBackground = None
        self.MessageAfterBackground = None
        self.fcnPlotOptions = None
        self.runVaryCommand = None
        self.delayBetweenRuns = None

        # below sets run specific values
        self.createObject()

        self.overwrite = False  # Set to true to delete previous runs
        self.bTakeData = bTakeData
        self.bAnalyzeData = bAnalyzeData
        self.TEST_ON_MAC =  False
        

        # Some routine use an SRS DG645 box:
        self.DG_IP_ADDR = "192.168.11.225"   # default
        config = configparser.ConfigParser()
        iniFile = r"config.ini"
        ret = config.read(iniFile)
        if ret:
            kPeripheral = 'Peripheral'
            kIP = 'IP'
            self.DG_IP_ADDR = config[kPeripheral][kIP]
            if VERBOSE:
                print(f"Read INI file {iniFile} section: {kPeripheral} key:{kIP} = {self.DG_IP_ADDR}")

        else:
            if VERBOSE:
                print(f"**No config file found: ({iniFile}). Using defaults.")

            
        

        
        



    #
    # userFunction is called for each frame of a run ( assumes an external trigger )
    #
    def usrFunction_DGCmd( self,nLoop ):
        """ nLoop is the frame number. 
        Send a command to DG SRS at each frame - assumes Ext trigger.
        """
        
        print(f"Called userFunction n={nLoop}")
        self.dg.counter  = nLoop + 1
        c  = f"{self.innerVarCommand} {self.innerVarList[nLoop]}"  
        
        #s = f"BURC {self.dg.counter}" # Set the burst Count
        self.dg.send(c);
        self.dg.doTrigger()
        
    #
    # userFunction is called for each frame of a run ( assumes an external trigger )
    #
    def userFunctionB( self, nLoop ):
        """ nLoop is the frame number. 
        Send a command to xPAD at each frame.
        """ 
        print(f"Called userFunctionB n={nLoop}")
        c  = f"{self.innerVarCommand} {self.innerVarList[nLoop]}"  
        
        res = xd.run_cmd(c)
        self.dg.doTrigger()


    def createObject(self):
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        if self.strDescriptor == "Analyze_CeO2":
            self.setname = 'CornellTests_24-11-06'
                              
            self.runnames = [f'FG_CeO2_111_200_0p{j+1}ms_200ns_{j+4}' for j in range(9)]
            self.runnames += [f'FG_CeO2_111_200_{j+1}ms_200ns_{j+13}' for j in range(5)]

            self.nFrames = 17-3 # debug 17-4  # frames Per Run
            #TODO - set ROI as needed            
            self.roi = [90, 60, 10, 10]
            self.NCAPS = 8 # can this be pulled from file?
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 3  # use fourth dim to hold integration times
            self.fcnPlot = prettyPlot
            self.varList = [i+4 for i in range(self.nFrames)]
            self.TakeBG = True   # Will load in a background
            self.back_runnames = [f'BG_CeO2_111_200_0p{j+1}ms_200ns' for j in range(9)]
            self.back_runnames += [f'BG_CeO2_111_200_{j+1}ms_200ns' for j in range(5)]
            self.x_axis_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3, 4, 5]
            self.x_axis_values = self.x_axis_values[:self.nFrames] # clip if testing a subset 
            
            self.fcnPlotOptions = self.x_axis_values # this work?



  
        
            
        else:
             raise Exception(" !Unknown string! ") 




    #
    #
    #
    def takeBackground(self):
        setname = self.setname
        nFrames = self.nFrames

        if self.overwrite:
            # delete old runs
            for match in glob(f"{RAIDPATH}/set-{setname}/run-back"):
                shutil.rmtree(match)
                print(f"***DELETE RUN {match}")
      
            
        #
        # Run through list of commands - and send them to HW
        #
        for c in self.list_commands:
            res = xd.run_cmd( c  )    
            if res:
                raise Exception(" Error ")

        NRUNS = 1

        runname=f"-bg back"        
        res = xd.run_cmd( f"startrun {runname}"  )   
        if res:
            raise Exception(" Error ") 

        # Optionally set SRS options here and trigger SRS for each frame in the run
        # Loop <nFrames> times
        #  
        self.runCount = 0
        if self.runFrameCommand:
            for j in range(nFrames):
                self.runFrameCommand(j)
                time.sleep(.5)
                
        xd.run_cmd( f"status -wait" )
        self.runCount += 1

    #
    # 
    #     
    def takeData(self):
        """ 
        Run multiple Runs - issuing one command (one parameter) that changes
        at each run.
        overWrite. Set to 1 to delete previous Runs
        Return Number of runs completed.
        """

        setname = self.setname
        #runname = 
        nFrames = self.nFrames
        varRange = self.varList

        if 0:  # Dont delete anything ever !
            if self.overwrite:
                # delete old runs
                # rm -r "$RAIDPATH"/set-$setname/run-run_*
                for match in glob(f"{RAIDPATH}/set-{setname}/run-run_*"):
                    shutil.rmtree(match)
                    print(f"***DELETE RUN {match}")
      
        res = True
      
 
        #
        # Run through list of commands - and send them to HW
        #
        for c in self.list_commands:
            if VERBOSE:
                print(f"**RUN_CMD {c}")
            res = xd.run_cmd( c  )    # there may be a bug in mmcmd  - returns previous string output.
            if res:
                raise Exception(" Error ")

        if varRange is not None:
            NRUNS = len(varRange)

        #
        # Start a series of Runs
        #
        self.runCount = 0
        for i in range(1, NRUNS + 1):     
            # scan a parameter here. Pass in runVaryCommand and varRange
            if self.runVaryCommand:
                var = varRange[0]
                varRange = varRange[1:] # remove first element
                c  = f"{self.runVaryCommand} {var}"
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
            if self.runFrameCommand:
                for j in range(nFrames):
                    self.runFrameCommand(j)
                    time.sleep(.5)
                    
            xd.run_cmd( f"status -wait" )
            self.runCount += 1

            if self.delayBetweenRuns:
                if VERBOSE:
                    print(f"--Delay {self.delayBetweenRuns} seconds --")
                time.sleep( self.delayBetweenRuns )


       

        return  self.runCount
    
    
    #
    #
    #
    def Take_Data(self):
        """
        Take Data        
        """        

        if self.runFrameCommand :

            c = comObject( 1, self.DG_IP_ADDR )
            r = c.tryConnect()

            # Future me:  dg is used in userFunction to adjust SRS box at each run frame.

            self.dg = DG645( c )
            self.dg.counter = 0 # truly python hackery
            self.dg.send("*CLS") # Clear errors
         
  
        # Create new Runs
        # Returns a dictionary
        if self.TakeBG:
            if self.MessageBeforeBackground:
                input(self.MessageBeforeBackground)

            self.takeBackground()

            if self.MessageAfterBackground:
                input(self.MessageAfterBackground)

        takeDataRet = self.takeData( )
        return takeDataRet    

    #
    # 
    #         
    def Analyze_Data(self):
        """
        Load up the runs, and analyze
        """

        setname = self.setname
        
        NRUNS = len(self.varList) 
        NCAPS = self.NCAPS
       
        roiSum = None
        repeat = 0
        


        while True:
            title = ""
            runBase = 1
            backFile = None
            

            for runnum in range(NRUNS):
                runname = self.runnames[runnum]
                
                if self.TEST_ON_MAC: # Local Mac testing!
                    foreFile = f'/Users/yoram/Sydor/keckpad/30KV_1.5mA_40ms_f_00015001.raw' # check not sure...
                    
                else:
                    foreFile = f'{RAIDPATH}/set-{setname}/run-{runname}/frames/{runname}_{runBase:08d}.raw'
                    
                
                self.fore = BKL.KeckFrame( foreFile )
                if self.TakeBG and self.back_runnames:
                    back_runname = self.back_runnames[runnum]
                    backFile = f'{RAIDPATH}/set-{setname}/run-{back_runname}/frames/{back_runname}_{runBase:08d}.raw'
                    self.back =  BKL.KeckFrame( backFile )

                if VERBOSE:
                    print(f"Loaded up file: {foreFile}")

                numImagesF = self.fore.numImages 

                if self.nFrames  * self.NCAPS > 1000:
                    # we need to read mutiple raw files - only 1000 per file.
                    self.readAdditionalFiles = {
                        "baseFilenameF" : foreFile[:-12], "nJumpBy":1000,
                        "baseFilenameB" : backFile[:-12] if backFile else None
                    }
                    numImagesF = self.nFrames  * self.NCAPS


                
                if roiSum is None:
                    if self.roiSumNumDims == 3:
                        roiSum = np.zeros((NRUNS,numImagesF // NCAPS, NCAPS),dtype=np.double)
                    elif self.roiSumNumDims == 4:
                        roiSum = np.zeros((NRUNS,numImagesF // NCAPS, NCAPS, self.roi[2]),dtype=np.double)


                            
                        

                # create global big arrays to hold images
                self.foreStack = np.zeros((numImagesF // NCAPS, NCAPS,512,512),dtype=np.double)


                # Each time called, builds up data in data var/ roiSum.
            
                roiSum = self.fcnToCall( self, data = roiSum, runnum = runnum)

                if self.runVaryCommand:
                    title = f"{self.runVaryCommand} {self.varList}"

            
            #ENDFOR
            if hasattr(self, "newTitle"):
                title = self.newTitle + ":" + title

            
                
            #
            #  fcnPlot is the function to generate plot. It is defined in the IF's above.
            #
            self.fcnPlot (roiSum, title, options = self.fcnPlotOptions )
          

            if hasattr(self, "roiB"):
                # repeat the analysis with a second ROI
                repeat += 1  # 0 --> 1
                self.roi = self.roiB # redefine the ROI
                self.newTitle = "roiB"
                if repeat >= 2:
                    break
            else:
                break            
        # WHILE LOOP

        
        if hasattr(self, 'fcnPlot2'):
            self.fcnPlot2 ( self, self.secondAnalysis, title = self.secondTitle ) 
            
            
        plt.show()    
        
        




#
# not used 
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
         # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        cnum = fIdex % 8
        backStack[ mdB.frameNum-1,cnum,:,:] += np.resize(dataB,[512,512])

    avgBack = backStack/( back.numImages/8.0)

    for fIdex in range( fore.numImages):
        (mdF,dataF) = fore.getFrame()
        # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        cnum = fIdex % 8

        foreStack[mdF.frameNum-1,cnum,:,:] += np.resize(dataF,[512,512])

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
    #plt.show()
 

#
# 
#    
def imagePlots(dobj, img, title):
    """
    Plot the standard deviation as an image for 8 caps
    """

    indexVal = 0
    c = 0
    fig,ax = plt.subplots(2,4)
    # Set the main title for the entire figure
    fig.suptitle(title)

    #  CLIPPING  If std dev plot appears at a fixed value it is becauyse it is clipped here
    vmin= 0
    vmax = 40

    for indexVal in range(8):
        indexRow = int(indexVal/4) 
        indexCol = int(indexVal%4)
        
        image = ax[indexRow,indexCol].imshow( np.clip(\
            img[c, :, :], vmin, vmax) ,\
                cmap = "viridis")
        image.set_clim(vmin, vmax)

        if indexCol == 0:
            # Add a colorbar
            # Optionally, set the colorbar scale explicitly
            cbar = fig.colorbar(image, aspect=4, ax = ax[indexRow,indexCol] )
      
        
        c += 1

    # endfor 
    fig.set_size_inches(12, 4)    
    fig.subplots_adjust(wspace = 0.645, hspace = -0.2) # space is padding height
    plt.tight_layout()

    
    

    
        
            
  

#
# Plot <n> caps. Plot mean of ROI versus frame number
#  data is 3 dimensions: data should be [nRuns, nFrames, nCaps]
# options can be self.x_axis_values[]
def prettyPlot(data, title, options = None):
    nruns = len(data)
    ncaps = len(data[0,0] )
    fig, ax = plt.subplots()
    #plt.figure(1)
    averageOverFrames = np.zeros(nruns,dtype=np.double)
    
    colors = ['r', 'orange','y', 'g', 'b', 'violet', 'indigo', 'black'] 
    nframes = len(data [0])
    
    xrange = range(nruns)
    if options is not None:
        arr = np.array(options)
        if arr.ndim == 1 and np.issubdtype(arr.dtype, np.floating):
            xrange = options
            # options is a 1D array of floats
            pass
    for c in range(ncaps):
        for n in range(nruns):
            
            # average the mean over all n frames
            averageOverFrames[n] = np.average(data[n, :, c])

        lbl = f"Cap:{c+1}"   
        ax.plot( xrange,  averageOverFrames[:], 
                color=colors[c], label = lbl )


    plt.legend()
    plt.xlabel('N')
    plt.ylabel('mean (ADU)')
    plt.title( title )
    ax.yaxis.set_minor_locator( MultipleLocator(1000))

    
    #plt.show(block= True) 



#
# Plot <n> caps. Plot mean of ROI versus frame number
#  data is 3 dimensions: data should be [nRuns, nFrames, nCaps]
# like prettyplot, but each run is appended in the list along the x axis
def prettyPlot_TODO(data, title, options = None):
    nruns = len(data)
    ncaps = len(data[0,0] )
    fig, ax = plt.subplots()
    #plt.figure(1)

    for n in range(nruns):    
        nframes = len(data [0])
        for c in range(ncaps):

            x = .5 +.5*(n / (nruns))
            if c%5 == 0:
                clr = (x,0,0)
            elif c%5 == 1:
                clr = (x,x,0)
            elif c%5 == 2:
                clr = (0,x,0)
            elif c%5 == 3:
                clr = (0,x,x)
            elif c%5 == 4:
                clr = (0,0,x)

            lbl = ""
            if n == 0:
                lbl = f"Cap:{c+1}"   

            xrange = range(n*nframes, (n+1)*nframes, 1)     

            ax.plot( xrange, data[n,:,c], 
                color=clr, label = lbl )


    plt.legend()
    plt.xlabel('N')
    plt.ylabel('mean (ADU)')
    plt.title( title )
    ax.yaxis.set_minor_locator( MultipleLocator(1000))

    
    #plt.show(block= True) 

#
#   TODO
#
def prettyCapVsFrame(data, title, options = None):
    """
    data should be [nRuns, nFrames, nCaps, Width_of_lineout]
    optional fcnPlotOptions = {"waterfall":5000}
    """
    nruns = len(data)

    fig, ax = plt.subplots()
    #plt.figure(1)
    nframes = len(data[0])
    ncaps = len(data[0,0] )
    dataWidth = len(data[0,0,0])
    deltaY = 0
    c = 1

    for n in range(nruns):     
        for f in range(nframes):
            d = []    
            d.extend( f*deltaY + data[n, f, c, :])
            
            x = .5 +.5*(f / (nframes-1))
            if f%3 == 0:
                clr = (x,0,0)
            elif f%3 == 1:    
                clr = (0,x,0)
            elif f%3 == 2:
                clr = (0,0,x)

            ax.plot( range(len(d)), d, color=clr, linewidth=0.5,
            label=f"Run{n}" if f ==0 else "" )



    plt.legend()
    plt.xlabel(f'Cap{c} versus Frame')
    plt.ylabel('Ave (ADU)')
    plt.title( title )
    ax.yaxis.set_minor_locator( MultipleLocator(1000))
    #plt.show(block=True) 


#
#   Data has <NCAPS> lineouts.  Line them all up into one lineout per image 
#
def prettyAllCapsInALine(data, title, options = None):
    """
    data should be [nRuns, nFrames, nCaps, Width_of_lineout]
    optional fcnPlotOptions = {"waterfall":5000}
    """
    nruns = len(data)

    fig, ax = plt.subplots()
    #plt.figure(1)
    nframes = len(data[0])
    ncaps = len(data[0,0] )
    dataWidth = len(data[0,0,0])
    deltaY = 0

    if options:
        deltaY = options.get("waterfall")


    for n in range(nruns):     
        for f in range(nframes):
            d = []    
            for c in range(ncaps):
                d.extend( f*deltaY + data[n, f, c, :])
            
            x = .5 +.5*(f / (nframes-1))
            if n%3 == 0:
                clr = (x,0,0)
            elif n%3 == 1:    
                clr = (0,x,0)
            elif n%3 == 2:
                clr = (0,0,x)

            ax.plot( range(len(d)), d, color=clr, linewidth=0.5,
            label=f"Run{n}" if f ==0 else "" )



    plt.legend()
    plt.xlabel('1Tap-lineout across ALL caps')
    plt.ylabel('Ave (ADU)')
    plt.title( title )
    ax.yaxis.set_minor_locator( MultipleLocator(1000))
    #plt.show(block=True) 

#
#  Used with Cornell_Noise
#
def calcBackgroundStats(dobj, data=None, runnum = 0):
    """
   
    title 
    data is [#run, #frame, #cap]
    runnum increments from 0 to #run-1
    NOTE - 
    """
   
    back = None
    
    if hasattr(dobj, "back"):
        back = dobj.back

    fore = dobj.fore
    roi = dobj.roi
    ncaps = dobj.NCAPS
    ave = np.zeros((8,512,512),dtype=np.double)
    imageCount = 0
    
    loopAgain = False
    raf = None   # Read Additional Files - needed when taking more than 1000 frames.
    runBase = 1

    try:
        raf = dobj.readAdditionalFiles
    except:
        pass

    loopAgain = True

    # Special case when more than 1000 frames are taken, we need to loop over multiple files. 
    while loopAgain:
        for fIdex in range( fore.numImages):
            (mdF,dataF) = fore.getFrame()
            if back:
                (mdB,dataB) = back.getFrame()
                dataF = dataF - dataB #  Put F-B in F as a kludge.

            frameNum = (runBase-1  + fIdex) // ncaps  # not a typo "//" is integer division 
            dataArray = np.resize(dataF,[512,512])
             # 12/27/23 oh oh mdb.capNum appears to be incorrect!
            cnum = fIdex % 8
            dobj.foreStack[frameNum,cnum,:,:] = dataArray
            ave[ cnum,:,:] += dataArray
            imageCount += 1

        if raf:
            runBase += raf["nJumpBy"]
            nextFileName = raf["baseFilenameF"] + f"{runBase:08d}.raw"
            try:
                fore = dobj.fore = BKL.KeckFrame( nextFileName )
                if VERBOSE:
                    print(f"Open Foreground:{nextFileName}")
            except Exception as e:
                loopAgain = False

            if back:
                nextFileName = raf["baseFilenameB"] + f"{runBase:08d}.raw"
                try:
                    back = dobj.back = BKL.KeckFrame( nextFileName )
                    if VERBOSE:
                       print(f"Open Background:{nextFileName}")

                except Exception as e:
                    loopAgain = False

        else:
            loopAgain = False
            break  # EXIT WHILE

        
        
    # WHILE } 

    for ic in range( ncaps ):
        ave[ ic, :, :] = ave[ ic, :, :] / (imageCount/ncaps)


    #dobj.ave = ave  # Python is awesome - just attach this new thing to the object.

    # rio is [X,Y,W,H]
    startPixY = roi[1]
    endPixY = startPixY + roi[3]
    startPixX = roi[0]
    endPixX = startPixX + roi[2]
    nImages =  imageCount // ncaps  # not a typo "//" is integer division 
    

    for fn in range( nImages ): 
        for cn in range (ncaps):
            V = np.average( dobj.foreStack[fn, cn, startPixY:endPixY, startPixX:endPixX] ) - \
                np.average( ave[cn, startPixY:endPixY, startPixX:endPixX] )
            data[runnum, fn,cn] = V
            #print( fn, cn, roiSum)


    if not hasattr(dobj, "secondAnalysis"):
        # Secondary analysis here?
        # We want RMS of each pixel.
        rmsPixels = np.zeros((8,512,512),dtype=np.double) # 8 CAPS, imageH, imageW
        
        print("--- this takes a long time ~ 30 seconds ---")

        img2 = np.zeros( (nImages, ncaps, 512, 512), dtype = np.double)
        for cn in range (ncaps):
            for fn in range( nImages ): 
                img2[fn, cn, :, :] = dobj.foreStack[fn, cn, :, :] - ave[cn, :, :]
            rmsPixels[cn, :, :] = np.std( img2[:, cn, :, :], axis = 0 )

        dobj.secondAnalysis = rmsPixels
    
    

    return data

def calcMeanVersusTime(dobj, data=None, runnum=0):
    """
    
    """
    if hasattr(dobj, "back"):
        back = dobj.back

    fore = dobj.fore
    roi = dobj.roi
    ncaps = dobj.NCAPS


    for fIdex in range( fore.numImages):
        (mdF,dataF) = fore.getFrame()
        if back:
            (mdB,dataB) = back.getFrame()
            dataF = dataF - dataB #  Put F-B in F as a kludge.

        frameNum = fIdex // ncaps  # not a typo "//" is integer division 
        dataArray = np.resize(dataF,[512,512])
        # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        cnum = fIdex % 8

        dobj.foreStack[frameNum,cnum,:,:] = dataArray

    #  [ Frame, Cap, Y , X ] 
    
    # ROI is [X,Y,W,H]
    startPixY = roi[1]
    endPixY = startPixY + roi[3]
    startPixX = roi[0]
    endPixX = startPixX + roi[2]
    nImages =  fore.numImages // ncaps  # not a typo "//" is integer division 
    

    for fn in range( nImages ): 
        for cn in range (ncaps):
            data[runnum, fn,cn] = np.average( dobj.foreStack[fn, cn, startPixY:endPixY, startPixX:endPixX] )
            #print( fn, cn, roiSum)

    return data



def calcLinearity(dobj, data=None, runnum = 0):
    """
    data is [#run, #frame, #cap]
    runnum increments from 0 to #run-1
    NOTE - Data is stored in array data.
    stores the average value over the ROI.
    """
   
    back = None
    
    if hasattr(dobj, "back"):
        back = dobj.back

    fore = dobj.fore
    roi = dobj.roi
    ncaps = dobj.NCAPS


    for fIdex in range( fore.numImages):
        (mdF,dataF) = fore.getFrame()
        if back:
            (mdB,dataB) = back.getFrame()
            dataF = dataF - dataB #  Put F-B in F as a kludge.

        frameNum = fIdex // ncaps  # not a typo "//" is integer division 
        dataArray = np.resize(dataF,[512,512])
        # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        cnum = fIdex % 8
        dobj.foreStack[frameNum,cnum,:,:] = dataArray


    # optionaly  compute the average of just the first run, and use that as the background
    # for all subsequent runs
    if hasattr(dobj, "computeBackgroundFromFirstRun") and runnum == 0:
        ave = np.zeros((8,512,512),dtype=np.double)
        for fIdex in range( fore.numImages):
            frameNum = fIdex // ncaps
            c = fIdex % ncaps
            ave[c, :, :] += dobj.foreStack[frameNum,c,:,:]

        ave = ave /  (fore.numImages / ncaps)   
        dobj.backFromFirstRunAve = ave 
    #  [ Frame, Cap, Y , X ] 
    

    if hasattr(dobj, "backFromFirstRunAve"):
        for fIdex in range( fore.numImages):
            frameNum = fIdex // ncaps
            c = fIdex % ncaps
            dobj.foreStack[frameNum,c,:,:] -=  dobj.backFromFirstRunAve[c, :, :]
        
    # rio is [X,Y,W,H]
    startPixY = roi[1]
    endPixY = startPixY + roi[3]
    startPixX = roi[0]
    endPixX = startPixX + roi[2]
    nImages =  fore.numImages // ncaps  # not a typo "//" is integer division 
    

    for fn in range( nImages ): 
        for cn in range (ncaps):
            data[runnum, fn,cn] = np.average( dobj.foreStack[fn, cn, startPixY:endPixY, startPixX:endPixX] )
            #print( fn, cn, roiSum)

    return data


def calcEachCapLineout(dobj,  data=None, runnum = 0):
    """
    data is [#run, #frame, #cap] = [list of data]
    runnum increments from 0 to #run-1
    NOTE - Data is stored in array data. Each element [r,f,c] is a list of values.
    
    """
   
    back = None
    fore = dobj.fore
    if hasattr(dobj, "back"):
        back = dobj.back
    roi = dobj.roi

    ncaps = dobj.NCAPS

    for fIdex in range( fore.numImages):
        (mdF,dataF) = fore.getFrame()
        if back:
            (mdB,dataB) = back.getFrame()
            dataF = dataF - dataB #  Put F-B in F as a kludge.

        frameNum = fIdex // ncaps  # not a typo "//" is integer division 
        # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        cnum = fIdex % 8

        dataArray = np.resize(dataF,[512,512])
        dobj.foreStack[frameNum,cnum,:,:] = dataArray

    #  [ Frame, Cap, Y , X ] 
    
    # rio is [X,Y,W,H]
    startPixY = roi[1]
    endPixY = startPixY + roi[3]
    startPixX = roi[0]
    endPixX = startPixX + roi[2]
    nImages =  fore.numImages // ncaps  # not a typo "//" is integer division 
    

    for fn in range( nImages ): 
        for cn in range (ncaps):
            # Hopefully - axis=0 averages over columns
            data[runnum, fn,cn] = np.mean( dobj.foreStack[fn, cn, startPixY:endPixY, startPixX:endPixX], axis=0 )
            #print(f"debug:{data[runnum, fn, cn]}")

    return data







def defineListOfTests():
    """
    Create a list of (string,string) that DEFINES the 
    Take or Analyze data routines, and give each a text description
    NOTE that the string MUST match those in createObject
    """

    lot = []
    lot.append( ("Analyze_CeO2", "Linearity vs  integration time.") )
    
    
    return lot


               


# Entry point of the script
if __name__ == "__main__":
    # Code to be executed when the script is run directly
    print("Start.")
 
    # 
    # Create a list of possible actions - and display a modal
    #
    lot = defineListOfTests()
    ui = UI_utils.UIPage( lot )
    ui.show()
    if ui.cancelled:
        exit(0)

        
    strDescriptor = ui.selectedText
    bTakeData,bAnalyzeData = ui.selectedActions

    print(f"I will run {strDescriptor} and " + "Take Data" if bTakeData else "" + "  Analyze Data" if bAnalyzeData else "" )


    #
    # Do the things
    #
    dobj = dataObject( strDescriptor, bTakeData=bTakeData, bAnalyzeData=bAnalyzeData)
    
    if dobj.bTakeData:
        ret = dobj.Take_Data()
        if ret == 0:
            exit(0)
        
    if dobj.bAnalyzeData:
        ret = dobj.Analyze_Data()
      
       

    print("Done!")     




#!/usr/bin/env python3
# File: TXC_010_Analysis.py
# Description - Create a list of analysis routines for the Transparent X-ray C-thing
#
# History
# v 1.0 28OCT2025 - Created.  Copied over from LLNL_020_Analysis.py

# ***** git instructions *****
#  If weirdness you may need this - but probably not.
# git checkout HEAD -- plotlineout_oop.py   (any file name)
# Normally just this to pull over changes from the cloud
# git stash
# git fetch
# git checkout origin/yf-newcode


# MAC Instructions.
# Use shift-Command P, and select /opt/homebrew/bin/python3  (v 3.13.1) - meh
# Use shift-Command P, and (3.11.4) (.venv) ./venv/bin/python - yes

#
# INSTRUCTIONS
#
# Look for SAVE_TO_DISK.
# Set accordingly. True takes long time to take data and saves to PKL file.
# False is fast and loads from PKL file.


# Python bit of workaround to load modules from the parent folder

import sys
import os

# Get the parent directory and add it to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

import pandas as pd
import configparser
import UI_utils
import time
import pickle
from glob import glob
import xpad_utils as xd
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import matplotlib.pyplot as plt
import shutil
import numpy as np

# Try to fix  self-closing plot window bug
import matplotlib
matplotlib.use("TkAgg")    # or "Qt5Agg" depending on what you have installed

#
# Define some globals
#
VERBOSE = 1  # 0 = quiet, 1 = print some, 2 = print a lot
PREVIEW_IMAGE = 1  # 0 = no preview, 1 = preview each image as loaded
#
#
# User edit settings
# Setting for 'Z drive'
# RAIDPATH=r"\\SYDOR-NAS01\RawDataBackup\CHESS_Nov2024\sydor_keck_data"
# Setting for local Mac
RAIDPATH = '/Volumes/TOSHIBA EXT_Beige/CHESS_Nov2024/sydor_TXC_data/TXC_CHESS_NOV2024/08NOV2024_testdata/'
# 08NOV2024_testdata/ChangingEnergies/20keV/Averaging/Beam0.6x1_8fps_avg10_low3high247.raw'
#
#
#   Set below true to oad files (takes a long time) and save to Pickle file
#   Then re run with it set to False to load from Pickle file (fast)
SAVE_TO_DISK = True

print(RAIDPATH)
exit
#
#
#

# OOP the heck out of this


class dataObject:
    def __init__(self, strDescriptor,
                 bTakeData=False, bAnalyzeData=False):
        self.strDescriptor = strDescriptor
        self.dg = None  # Optional Delay Generator
        self.TakeBG = False
        self.MessageBeforeBackground = None
        self.MessageAfterBackground = None
        self.fcnPlotOptions = {}
        self.runVaryCommand = None
        self.delayBetweenRuns = None
        self.pickleFilename = "DUMP"
        

        # below sets run specific values
        self.createObject()

        self.overwrite = False  # Set to true to delete previous runs
        self.bTakeData = bTakeData
        self.bAnalyzeData = bAnalyzeData
        self.TEST_ON_MAC = False

        # You must set these manually . Set bSaveToDisk once to run the
        # long operation once, and save to PKL file.
        # Then set it false, and set bLoadFromDisk to use the PKL file.
        self.bSaveToDisk = SAVE_TO_DISK
        self.bLoadFromDisk = not self.bSaveToDisk
        #
        #
        #

      #   # Some routine use an SRS DG645 box:
      #   self.DG_IP_ADDR = "192.168.11.225"   # default
      #   config = configparser.ConfigParser()
      #   iniFile = r"config.ini"
      #   ret = config.read(iniFile)
      #   if ret:
      #       kPeripheral = 'Peripheral'
      #       kIP = 'IP'
      #       self.DG_IP_ADDR = config[kPeripheral][kIP]
      #       if VERBOSE:
      #           print(f"Read INI file {iniFile} section: {kPeripheral} key:{kIP} = {self.DG_IP_ADDR}")

      #   else:
      #       if VERBOSE:
      #           print(f"**No config file found: ({iniFile}). Using defaults.")

    def createObject(self):
        # *******************11111111111**********************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        if self.strDescriptor == "20keV_average":
            # these are all ChangingEnergies/20keV/Averaging
            
            #self.setname = 'ChangingEnergies/20keV/Averaging/Beam0.6x1_8fps_avg10_low3high247.raw'
            #self.setname = 'ChangingEnergies/20keV/Averaging/Beam0.6x1_8fps_avg20_low0high247.raw'
            self.setnames = [\
                'ChangingEnergies/20keV/Averaging/Beam0.6x1_8fps_avg10_low3high247.raw',
                'ChangingEnergies/20keV/Averaging/Beam0.6x1_8fps_avg20_low0high247.raw',
                'ChangingEnergies/20keV/Averaging/Beam0.6x1_8fps_avg20_low3high247.raw'
            ]

            

            self.roi = []

            self.fcnToCall = calcCoM
            
            #
            self.fcnPlot = prettyPlot    
            self.fcnPlotOptions["xrayEnergy"] = "20"
            self.fcnPlotOptions["beamsize"]   = ".6x1.0"
            self.dim2size = 3


            #

        # ****************************************************
        # ****************** 2222222222 **********************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        elif self.strDescriptor == "40keV_average":
           #'   'ChangingEnergies/42keV/Averaging/JustCollectingAWhile.raw'
            
          
            self.setnames = [\
                'ChangingEnergies/42keV/Averaging/AlumFilter0-18_avg20_3-319.raw',
                'ChangingEnergies/42keV/Averaging/Beam0.6x1_8fps_avg20_low3high319.raw',
                'ChangingEnergies/42keV/Averaging/Beam1x1_8fps_avg20_low3high247.raw',
                'ChangingEnergies/42keV/Averaging/JustCollectingAWhile.raw'
            ]

            

            self.roi = []

            self.fcnToCall = calcCoM

            #
            self.fcnPlot = prettyPlot    
            self.fcnPlotOptions["xrayEnergy"] = "42"
            self.fcnPlotOptions["beamsize"]   = ".6x1.0"
            self.dim2size = 3
    

        # ****************************************************
        # ****************** 333333333  **********************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        elif self.strDescriptor == "flux_mode analysis":
           #'   'ChangingEnergies/42keV/Averaging/JustCollectingAWhile.raw'
            
          
            self.setnames = [\
                'ChangingEnergies/20keV/MediumGain/15fps/Flux_15fps-1500_att0-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/Flux_15fps-1500_att0-1_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/Flux_15fps-1500_att10-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/Flux_15fps-1500_att17-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/Flux_15fps-1500_att5-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att0-0_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att0-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att0-1_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att0-1_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att10-0_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att10-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att17-0_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att17-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att5-0_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/15fps/LV_15fps-1500_att5-0_biason_gainM.raw'      
            ]

            

            self.roi = [15,0,2,32]

            self.fcnToCall = calcEvsT
            
            #
            self.fcnPlot = prettyPlot2    
            self.fcnPlotOptions["frameMax"] = 10
            self.fcnPlotOptions["fps"] = 15
            
            self.dim2size = 32


        # ****************************************************
        # ****************** 444444444  **********************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        elif self.strDescriptor == "flux_mode_at_21Hz_analysis":
           #'   'ChangingEnergies/42keV/Averaging/JustCollectingAWhile.raw'
            
            """
            
            """
          
            self.setnames = [\
                'ChangingEnergies/20keV/MediumGain/21fps/flux_21fps-2300_att0-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/flux_21fps-2300_att0-1_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/flux_21fps-2300_att10-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/flux_21fps-2300_att17-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/flux_21fps-2300_att5-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att0-0_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att0-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att0-1_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att0-1_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att10-0_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att10-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att17-0_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att17-0_biason_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att5-0_biasoff_gainM.raw',
                'ChangingEnergies/20keV/MediumGain/21fps/LV_21fps-2300_att5-0_biason_gainM.raw'
                ]

            

            self.roi = [15,0,2,32]

            self.fcnToCall = calcEvsT
            
            #
            self.fcnPlot = prettyPlot2    
            self.fcnPlotOptions["frameMax"] = 10
            self.fcnPlotOptions["fps"] = 21
            
            self.dim2size = 32



        

        else:
            raise Exception(" !Unknown string! ")
        

       





    #
    #
    #

    def Analyze_Data(self):
        """
        Load up the runs, and analyze
        """

        for sn in range ( len( self.setnames) ):
            setname = self.setnames[sn]

            roiSum = None
            repeat = 0

            dt = np.dtype('<i4')
            
            title = ""
            runBase = 1
            backFile = None

            if self.bSaveToDisk:

                foreFile = f'{RAIDPATH}/{setname}'
                indata = np.fromfile(foreFile, dtype=dt)
                
                self.numImagesF = len(indata)//(32*32) # '//' required!
                self.fore = np.resize(indata, [self.numImagesF,32, 32])

                if VERBOSE:
                    print(f"Loaded up file: {foreFile}")
                    print("debug", indata[0:31] )

                array_size = (self.numImagesF, self.dim2size)
                data2 = np.zeros( array_size,dtype=np.double)                
                data3 = self.fcnToCall( self, data = data2)    
                 
                self.fcnPlotOptions["filename"] = setname
                self.fcnPlot (data3, "title",  options = self.fcnPlotOptions )

                    

            elif self.bLoadFromDisk:
                # Load from Pickle file
                roiSum = loadData(self.pickleFilename)
                title = self.fcnPlotOptions["title"]

            
                
                self.fcnPlot (data3, "title",  options = self.fcnPlotOptions )

                

            plt.show(block=True)


#
# not used
#
def plotROI(cap, zSX, zSY, nTap, W, H):
    """ cap is cap 0-7
        zSX and zSY are 0-3 ASIC coordinate
        nTap is 1-8
        W,H are in pixels typ 128,16
    """
    global foreStack, backStack, fore, back
    ##################################
    # Adjust for clipping
    ##################################
    clipHigh = 1e8
    clipLow = 0
    # read all the image files
    for fIdex in range(back.numImages):
        (mdB, dataB) = back.getFrame()
        #  return frameParms, lengthParms, frameMeta, capNum, data, frameNum, integTime, interTime
        # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        cnum = fIdex % 8
        backStack[mdB.frameNum-1, cnum, :, :] += np.resize(dataB, [512, 512])

    avgBack = backStack/(back.numImages/8.0)

    for fIdex in range(fore.numImages):
        (mdF, dataF) = fore.getFrame()
        # 12/27/23 oh oh mdb.capNum appears to be incorrect!
        cnum = fIdex % 8

        foreStack[mdF.frameNum-1, cnum, :, :] += np.resize(dataF, [512, 512])

    # standDev = np.zeros((8,512,512),dtype=np.double)
    DiffStack = foreStack-backStack
    # asicSDs = np.zeros((8,16),dtype=np.double)

    #  [ Frame, Cap, Y , X ] # TODO: check Y,X is correct
    PerCapImage = DiffStack[:, cap, :, :]

    startPixY = zSY * 128 + (nTap-1) * 16
    endPixY = startPixY + H
    startPixX = zSX * 128
    endPixX = startPixX + W
    # frame 0 hardcoded for now
    #                       frame  ,     Y,   X
    # might be flipped?? #WIP#
    plt.imshow(PerCapImage[0, startPixY:endPixY, startPixX:endPixX])
    # TODO - we want to measure the amount of gradient, and average them over N Frames - toss out first image.
    # x axis is <varRange>  y axis is <entity> x 8 for each Cap.
    ave_over_frames = DiffStack[:, cap, startPixY:endPixX, startPixX:endPixX].mean(
        axis=0)  # Take average over rows
    # does this give me a 1-D over x?
    data_array = ave_over_frames.mean(axis=0)
    # Not sure ^ if thats right.

    xd.gradient_over_lineout(data_array)
    # plt.show()


#
#
#
def imagePlots(dobj, img, title):
    pass



def loadData(fname):
    """ 
    Load data from a pickle file
    """
    filename = "DUMP.pkl" if fname is None else fname.replace(
        " ", "_") + ".pkl"
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    print(f"Loaded data from {filename}")
    return data


def saveData(data, fname, options=None):
    """ 
    Save data to a pickle file
    """
    filename = "DUMP.pkl" if fname is None else fname.replace(
        " ", "_") + ".pkl"

    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f"Saved data to {filename}")


#
#
#  data is 3 dimensions: data should be [nRuns, nFrames, nCaps]
#     options {"integ": #, "inter":#}
#
def ringWalkPlot(data, title, options: dict):
    nruns = data.shape[0]
    nframes = data.shape[1]
    ncaps = data.shape[2]
    dT = 10  # time between runs in ns

    phase = 0
    # Require  dict with these defined
    integTime = options["integ"]
    interTime = options["inter"]
    plt.figure(figsize=(8, 5))  # width=8 inches, height=5 inches

    colors = ['r', 'orange', 'y', 'g', 'b', 'violet', 'indigo', 'black']
    for c in range(ncaps):
        phase = 0
        xvalue = np.zeros(nruns)
        yvalue = np.zeros((nruns, nframes))
        for n in range(nruns):
            phase += dT  # in ns

            # assumes integ and inter are constant
            cphase = phase + (integTime + interTime) * c
            xvalue[n] = cphase
            # stddev = np.std(data[n, :, c])
            # yvalue[n] = [np.mean(data[n, :, c])+stddev, np.mean(data[n, :, c])- stddev]
            yvalue[n] = data[n, :, c]

        # plt.plot( xvalue, yvalue,
        #         color = colors[c], label = f"Cap {c+1}" )

        plt.plot(xvalue, yvalue, color=colors[c])
        # only label once
        plt.plot([], [], color=colors[c], label=f"Cap {c+1}")

        # endfor c
    # endfor n

    plt.xlabel("Delay in (ns)")
    plt.ylabel("Mean ADU")
    plt.title(title)

    # plt.legend(loc='upper right', bbox_to_anchor=(1, 0.5))
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1))

    plt.grid()
    plt.show(block=False)




#
# Plot Vertical lienout as a ENergy vs Time plot
#  

def prettyPlot2(data, title, options: dict):
    """
    self.fcnPlotOptions["frameMax"] = "10"
    """


    nFrames = data.shape[0]
    #xrange = range(nFrames)
    fps = options.get("fps",1)  # Its not clear how much time passes between 2 frames?

    
    frameMax = options.get("frameMax", nFrames)

    

    # ---------------- FIGURE 1: X and Y center of mass ----------------
    fig1, ax1 = plt.subplots()
    
    # The TXC hardware takes rowss per 'frame', so at x FPS it is running at X x 34 rows /sec
    for run in range(frameMax):
        xrange = (np.arange( 32 ) + 32*run) * (1/(34*fps)) * 1000 # convert to ms.
        ax1.plot(xrange, data[run, 0:32], label=f"run {run}")
        

    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Intensity")
    ax1.set_title("'flux mode' Intensity vs Time")
    #ax1.yaxis.set_minor_locator(MultipleLocator(1000))
    
    
    fig1.canvas.manager.set_window_title(options.get("filename", "figure"))

    ax1.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    ax1.grid(True)

    plt.show(block=True)

#
# Plot CoM x,y, and Intensity for every frame in the data
#  

def prettyPlot(data, title, options: dict):

    nFrames = data.shape[0]
    xrange = range(nFrames)

    # ---------------- FIGURE 1: X and Y center of mass ----------------
    fig1, ax1 = plt.subplots()
    ax1.plot(xrange, data[:, 0], label="X CoM")
    ax1.plot(xrange, data[:, 1], label="Y CoM")
    ax1.set_xlabel(options.get("x_axis_label", "N"))
    ax1.set_ylabel("Position (pixels)")
    ax1.set_title("X/Y Center of Mass")
    ax1.yaxis.set_minor_locator(MultipleLocator(1000))
    ax1.legend()
    ax1.grid(True)

    # ---------------- FIGURE 2: Intensity ----------------
    fig2, ax2 = plt.subplots()
    ax2.plot(xrange, data[:, 2], label="Intensity", marker='o')
    ax2.set_xlabel(options.get("x_axis_label", "N"))
    ax2.set_ylabel("Intensity (counts)")
    ax2.set_title("Intensity")
    ax2.legend()
    ax2.grid(True)

    filename = options.get("filename", "---")
    # Copy this print output to g sheet for later analysis
    #File	xray Energy	Beam Size	std x	std y	std illum	FPS	AVERAGE	LOW	HIGH
    xrayE = options.get("xrayEnergy", "?")
    beamsize = options.get("beamsize", "?x?")
    print(f"{filename}, {xrayE}, {beamsize}, {np.std(data[:, 0])}, \
          {np.std(data[:, 1])}, {np.std(data[:, 2])}" ) 
    plt.show(block=True)


# Wrap this code into it own function
#  # Read CSV file
#  #  # https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
def readCSV(filename):
    import pandas as pd

    # Path to your CSV file
    # This file uses the average of all the diode readings for ic0. Each Spec run starts
    # at the beginning of a run, so it roughtly matches in time
    # filename =
    # ^ Path might break if not running From the PAD_Analysis folder

    # Read the CSV into a DataFrame
    df = pd.read_csv(filename)

    # Display the contents
    print(df)  # DEBUG

    # Access columns as Series
    int_time = df["IntTime"]
    spec_num = df["SPEC#"]
    avg_diode = df["Average Diode Reading"]

    print("\nIntTime values:", int_time.to_list())
    print("Average Diode Readings:", avg_diode.to_list())

    first = avg_diode[0]
    normed_diode = [x / first for x in avg_diode]
    print("Normalized Diode Readings:", normed_diode)
    return normed_diode




#
#  For flux images, we do a vertical lineout (vertical represents time 
#  The frame rate determines the elapsed time.  Entire diamond energy is stored as one row
#  Take a vertical lineout through center, and store array of 32 times.
#  Energy vs Time
def calcEvsT(dobj, data:np.ndarray, runnum=0):
    """
    dObj contains [fore] is N x 32x32 x4 byte image stack
    data is [#frame, 32x32]   
    Calculate Energy vs Time, return as a 32 long vector
    """

    back = None

    if hasattr(dobj, "back"):
        back = dobj.back

    fore = dobj.fore
    roi = dobj.roi
   
   # We will assume the ROI is correct.  It should be about 2p wide, 32p high down the center 
    if roi is not None and len(roi) == 4:
        # rio is [X,Y,W,H]
        startPixY = roi[1]
        endPixY = startPixY + roi[3]
        startPixX = roi[0]
        endPixX = startPixX + roi[2]

    nImages = dobj.numImagesF
    indata = dobj.fore

    
    # if PREVIEW_IMAGE and runnum == 0:
    if PREVIEW_IMAGE:
        zproject = np.average(dobj.fore, axis=0)  # average over frames
        plt.imshow(zproject)
        plt.show(block=True)

   
    
    for n in range( nImages):        
        slice = indata[n]  # a 32x32 frame        
        # average over x dim
        vlineout = slice[startPixY:endPixY, startPixX:endPixX].mean(axis=1)

        data[n] = vlineout


    # ENDFOR    
    return data




#
#
#
def calcCoM(dobj, data:np.ndarray, runnum=0):
    """
    dObj contains [fore] is N x 32x32 x4 byte image stack
    data is [#frame, 32x32]   
    Calculate Center Of Mass , and TBD
    """

    back = None

    if hasattr(dobj, "back"):
        back = dobj.back

    fore = dobj.fore
    roi = dobj.roi
   
    if roi is not None and len(roi) == 4:
        # rio is [X,Y,W,H]
        startPixY = roi[1]
        endPixY = startPixY + roi[3]
        startPixX = roi[0]
        endPixX = startPixX + roi[2]

    nImages = dobj.numImagesF
    indata = dobj.fore

    
    # if PREVIEW_IMAGE and runnum == 0:
    if PREVIEW_IMAGE:
        zproject = np.average(dobj.fore, axis=0)  # average over frames
        plt.imshow(zproject)
        plt.show(block=True)

    y_indices, x_indices = np.indices((32,32))
    y_indices = y_indices + 0.5 # Make this agree with imageJ
    x_indices = x_indices + 0.5
    
    
    for n in range( nImages):        
        slice = indata[n]  # a 32x32 frame        
        total = slice.sum()

        x_center = (x_indices * slice).sum() / total
        y_center = (y_indices * slice).sum() / total
        
        data[n] = x_center, y_center, (total/ (32*32))


    # ENDFOR    
    return data


def defineListOfTests():
    """
    Create a list of (string,string) that DEFINES the 
    Take or Analyze data routines, and give each a text description
    NOTE that the string MUST match those in createObject
    """

    lot = []
    lot.append(("20keV_average", "Plot stability of pointing and intensity.") )
    lot.append(("40keV_average", "Plot stability of pointing and intensity.") )
    lot.append(("flux_mode analysis", "Look at hi freq energy stability 15 Hz data.") )
    lot.append(("flux_mode_at_21Hz_analysis", "Look at hi freq energy stability 21Hz data.") )

    

    
    
        

    return lot


# Entry point of the script
if __name__ == "__main__":
    # Code to be executed when the script is run directly
    print("Start.")

    #
    # Create a list of possible actions - and display a modal
    #
    lot = defineListOfTests()
    ui = UI_utils.UIPage(lot)
    ui.show()
    if ui.cancelled:
        exit(0)

    strDescriptor = ui.selectedText
    bTakeData, bAnalyzeData = ui.selectedActions

    print(f"I will run {strDescriptor} and " +
          "Take Data" if bTakeData else "" + "  Analyze Data" if bAnalyzeData else "")

    #
    # Do the things
    #
    dobj = dataObject(strDescriptor, bTakeData=bTakeData,
                      bAnalyzeData=bAnalyzeData)

    if dobj.bTakeData:
        # ret = dobj.Take_Data()
        # if ret == 0:
            exit(0)

    if dobj.bAnalyzeData:
        ret = dobj.Analyze_Data()

    print("Done!")

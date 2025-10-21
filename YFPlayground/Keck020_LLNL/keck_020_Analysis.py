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
# Look for SAVE_TO_DISK.   
# Set accordingly. True takes long time to take data and saves to PKL file.
# False is fast and loads from PKL file.


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
import pandas as pd


#
# Define some globals 
#
VERBOSE = 1 # 0 = quiet, 1 = print some, 2 = print a lot
PREVIEW_IMAGE = 0 # 0 = no preview, 1 = preview each image as loaded
#
#
# User edit settings
# Setting for 'Z drive'
#RAIDPATH=r"\\SYDOR-NAS01\RawDataBackup\CHESS_Nov2024\sydor_keck_data"
# Setting for local Mac
RAIDPATH = '/Volumes/TOSHIBA EXT_Beige/CHESS_Nov2024/sydor_keck_data'

#
#  There are 7 RingWalk datums.  See https://docs.google.com/spreadsheets/d/1uVOXTLz-_K85X634gSuCnmFfIuGQfjPGFcuU3kh0qKk/edit?gid=817004952#gid=817004952
# for ID 1 to 7
#  Analyze RingWalk ID #
#
ARW_ID = 7 # 1  = Cornell_Tests_24-11-07_RW_FG_50ns_50ns
#          2  = Cornell_Tests_24-11-07_RW_FG_100ns_50ns
#          3  = Cornell_Tests_24-11-07_RW_FG_100ns_100ns    
#          4 = Cornell_Tests_24-11-07_RW_FG_100ns_200ns
#          5 = Cornell_Tests_24-11-06_RW_FG_150ns_200ns ! Missing data after TD340 :-(
#          6 = Cornell_Tests_24-11-07_RW_FG_200ns_200ns        
#          7= Cornell_Tests_24-11-07_RW_FG_300ns_200ns
#
#   Set below true to oad files (takes a long time) and save to Pickle file
#   Then re run with it set to False to load from Pickle file (fast)
SAVE_TO_DISK = False    


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
        self.fcnPlotOptions = {}
        self.runVaryCommand = None
        self.delayBetweenRuns = None
        self.pickleFilename = "DUMP"
        
        # below sets run specific values
        self.createObject()

        self.overwrite = False  # Set to true to delete previous runs
        self.bTakeData = bTakeData
        self.bAnalyzeData = bAnalyzeData
        self.TEST_ON_MAC =  False

        # You must set these manually . Set bSaveToDisk once to run the 
        # long operation once, and save to PKL file.
        # Then set it false, and set bLoadFromDisk to use the PKL file.    
        self.bSaveToDisk = SAVE_TO_DISK
        self.bLoadFromDisk =  not self.bSaveToDisk
        #
        #
        #

        

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

            self.nFrames = 9 + 5  # is the full data set. 
                  
            
            self.roi = [183,314,15,15]
            self.NCAPS = 8 # can this be pulled from file?
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 3  #
            ###self.roiSum_AttributeType = "ave,stdev" # make up a string that indicates the 
            #  typeof data this arrauy will hold.
            
           
            self.varList = [i+4 for i in range(self.nFrames)]
            self.TakeBG = True   # Will load in a background
            self.back_runnames = [f'BG_CeO2_111_200_0p{j+1}ms_200ns' for j in range(9)]
            self.back_runnames += [f'BG_CeO2_111_200_{j+1}ms_200ns' for j in range(5)]
    
            self.x_axis_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 2, 3, 4, 5]
            self.x_axis_values = self.x_axis_values[:self.nFrames] # clip if testing a subset 
            
            
            self.fcnPlotOptions["x_axis_values"] = self.x_axis_values
            self.fcnPlotOptions["x_axis_label"] = "Integration Time (ms)"
            self.fcnPlotOptions["title"] = "Counts vary linearly with integration time"
            self.fcnPlotOptions["energy_correction_filename"]  = "YFPlayground/Keck020_LLNL/Energy_Correction.csv"
            
        ##) 


             # Pass in the x axis values to plot.
            self.fcnPlot = prettyPlot
            self.pickleFilename = f"CeO2_Integ_scan"

           
        # ****************************************************
        # *******************222222***************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        elif self.strDescriptor == "Analyze_RingWalk":
            


            self.runnames = [f'scan_TD_{td}' for td in range(110,510,10)]
            self.nFrames = len ( self.runnames )  
            self.roiSumNumDims = 3  #
            self.varList = [i for i in range(self.nFrames)]
            self.integ = 0
            self.inter = 0

            self.TakeBG = True   # Will load in a background

            if ARW_ID == 1:
                self.roi = [279,188,2,2]  # Verify the spot doesn't move from run to run (!)
                self.setname = 'Cornell_Tests_24-11-07_RW_FG_50ns_50ns'
                # Ringwalks have their own background set!
                self.backSetName = 'Cornell_Tests_24-11-07_RW_BG_50ns_50ns'
                self.backRunName = 'back'
                self.integ = 50
                self.inter = 50

            elif ARW_ID == 2:
                self.roi = [279,188,2,2]  # Verify the spot doesn't move from run to run (!)
                self.setname = 'Cornell_Tests_24-11-07_RW_FG_100ns_50ns'
                # Ringwalks have their own background set!
                self.backSetName = 'Cornell_Tests_24-11-07_RW_BG_100ns_50ns'
                self.backRunName = 'Back'  # !F
                self.integ = 100
                self.inter = 50

            elif ARW_ID == 3:
                self.roi = [279,188,2,2]  # Verify the spot doesn't move from run to run (!)
                self.setname = 'Cornell_Tests_24-11-07_RW_FG_100ns_100ns'
                # Ringwalks have their own background set!
                self.backSetName = 'Cornell_Tests_24-11-07_RW_BG_100ns_100ns'
                self.backRunName = 'back'  
                self.integ = 100
                self.inter = 100    

            elif ARW_ID == 4:
                self.roi = [279,188,2,2]  # Verify the spot doesn't move from run to run (!)
                self.setname = 'Cornell_Tests_24-11-07_RW_FG_100ns_200ns'
                # Ringwalks have their own background set!
                self.backSetName = 'Cornell_Tests_24-11-07_RW_BG_100ns_200ns'
                #self.backRunName = 'back'   ! oops F!
                #del self.backRunName
                self.integ = 100
                self.inter = 200        
                self.back_runnames =  self.runnames

            elif ARW_ID == 5:
                self.roi = [279,188,2,2]  # Verify the spot doesn't move from run to run (!)
                self.setname = 'Cornell_Tests_24-11-07_RW_FG_150ns_200ns'
                # Ringwalks have their own background set!
                self.backSetName = 'Cornell_Tests_24-11-07_RW_BG_150ns_200ns'
                self.backRunName = 'back'  
                self.integ = 150
                self.inter = 200        
                
            elif ARW_ID == 6:
                self.roi = [279,188,2,2]  # Verify the spot doesn't move from run to run (!)
                self.setname = 'Cornell_Tests_24-11-07_RW_FG_200ns_200ns'
                # Ringwalks have their own background set!
                self.backSetName = 'Cornell_Tests_24-11-07_RW_BG_200ns_200ns'
                self.backRunName = 'back-002'  
                self.integ = 200
                self.inter = 200        

            elif ARW_ID == 7:
                # Extended run
                self.runnames = [f'scan_TD_{td}' for td in range(110,650+10-10,10)] 
                # 650 run is missing one frame, so skip it,               ^-10
                self.nFrames = len ( self.runnames )  
                self.roiSumNumDims = 3  #
                self.varList = [i for i in range(self.nFrames)]


                self.roi = [279,188,2,2]  # Verify the spot doesn't move from run to run (!)
                self.setname = 'Cornell_Tests_24-11-07_RW_FG_300ns_200ns'
                # Ringwalks have their own background set!
                self.backSetName = 'Cornell_Tests_24-11-07_RW_BG_300ns_200ns'
                self.backRunName = 'back'  
                self.integ = 300
                self.inter = 200        

            else:
                raise Exception(" !Unknown ARW_ID! ")


                
            self.NCAPS = 8 # can this be pulled from file?
            self.fcnToCall = calcLinearity 
            self.fcnPlot = ringWalkPlot   
            self.pickleFilename = f"ringwalk_{ARW_ID}"


            self.fcnPlotOptions["integ"] = self.integ
            self.fcnPlotOptions["inter"] = self.inter
            self.fcnPlotOptions["title"] = f"RingWalk. Plot intensity "\
                "versus delay.Integ = {self.integ} ns, Inter = {self.inter} ns"


           
        # ****************************************************
        # ******************* 333333 *************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        elif self.strDescriptor == "Ruby_integ_scan":

            self.setname = 'Cornell_Tests_24-11-08_INT_LIN_G1p0_Att00_TD0p2'
            # /run-BG_0p1us_100ns'
            #'set-/run-FG_0p1us_100ns'

            self.runnames = [f'FG_{x}us_100ns' for x in ["10","5","2","1", "0p5", "0p2", "0p1", "0p05"] ]
       

            self.nFrames = len(self.runnames)
                  
            
            self.roi = [270,181,25,25]
            self.NCAPS = 8 # can this be pulled from file?
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 3  #


            self.varList = [i for i in range(self.nFrames)]
            self.TakeBG = True   # Will load in a background
            self.backSetName = "Cornell_Tests_24-11-08_INT_LIN_G1p0_Att00"
            self.back_runnames = [name.replace("FG_", "BG_") for name in self.runnames]

            
    
            self.x_axis_values = [10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05]
            self.x_axis_values = self.x_axis_values[:self.nFrames] # clip if testing a subset 
            
            
            self.fcnPlotOptions["x_axis_values"] = self.x_axis_values
            self.fcnPlotOptions["x_axis_label"] = "Integration Time (ms)"
            self.fcnPlotOptions["title"] = "Counts vs integration time"    
            self.fcnPlotOptions["energy_correction_filename"]  = "YFPlayground/Keck020_LLNL/EC_Ruby.csv"
                

             # Pass in the x axis values to plot.
            self.fcnPlot = prettyPlot
            self.pickleFilename = f"ruby_integ_scan"


        # ****************************************************
        # ******************* 4444444 ************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        # ****************************************************
        elif self.strDescriptor == "Ruby_gain-lin":


            self.setname = 'Cornell_Tests_24-11-08_GAIN_bright_LIN_Att00_TD0p2'
            # /run-BG_0p1us_100ns'
            #'set-/run-FG_0p1us_100ns'
            gains = ["G1p0", "G0p429", "G0p250", "G0p153"]
            times = ["10", "5", "2", "1", "0p5", "0p2", "0p1", "0p05"]

            self.runnames = [f'FG_{t}us_100ns_{g}' for t in times for g in gains]

            self.nFrames = len(self.runnames)
                  
            
            self.roi = [283,187,2,2] 
            self.NCAPS = 8 # can this be pulled from file?
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 3  #


            self.varList = [i for i in range(self.nFrames)]
            self.TakeBG = True   # Will load in a background
            self.backSetName = self.setname
            self.back_runnames = [name.replace("FG_", "BG_") for name in self.runnames]

            
    
            self.x_axis_values = [x for x in [10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05] for _ in range(4)]
            self.x_axis_values = self.x_axis_values[:self.nFrames] # clip if testing a subset 
            
            
            self.fcnPlotOptions["x_axis_values"] = self.x_axis_values
            self.fcnPlotOptions["x_axis_label"] = "Normalized Values versus Gain"
            self.fcnPlotOptions["title"] = "Counts vs integration time & gain"    
            self.fcnPlotOptions["energy_correction_filename"]  = "YFPlayground/Keck020_LLNL/Gain_Lin.csv"
                

             # Pass in the x axis values to plot.
            self.fcnPlot = prettyPlot2
            self.pickleFilename = f"ruby_gain_scan"

            
                
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
            
            if self.bSaveToDisk:

                for runnum in range(NRUNS):
                    runname = self.runnames[runnum]
                    
                    if self.TEST_ON_MAC: # Local Mac testing!
                        foreFile = f'/Users/yoram/Sydor/keckpad/30KV_1.5mA_40ms_f_00015001.raw' # check not sure...
                        
                    else:
                        foreFile = f'{RAIDPATH}/set-{setname}/run-{runname}/frames/{runname}_{runBase:08d}.raw'
                        
                    
                    self.fore = BKL.KeckFrame( foreFile )
                    if self.TakeBG:

                        if  hasattr(self, 'backSetName') :
                            backSetName = self.backSetName
                            if  hasattr(self,'backRunName'):   
                                backFile = f'{RAIDPATH}/set-{backSetName}/run-{self.backRunName}/frames/{self.backRunName}_{runBase:08d}.raw'
                            else:
                                back_runname = self.back_runnames[runnum]
                                backFile = f'{RAIDPATH}/set-{backSetName}/run-{back_runname}/frames/{back_runname}_{runBase:08d}.raw'

                            self.back =  BKL.KeckFrame( backFile )

                        elif self.back_runnames:
                            back_runname = self.back_runnames[runnum]
                            backFile = f'{RAIDPATH}/set-{setname}/run-{back_runname}/frames/{back_runname}_{runBase:08d}.raw'
                            self.back =  BKL.KeckFrame( backFile )
                        else:
                            raise Exception(" No background run name defined ")
                        

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

                        # if self.roiSum_AttributeType == "ave,stdev"  :
                        #     # Allocate 0 index for AVE and 1 index for STDEV
                        #     roiSum = np.zeros((NRUNS,numImagesF // NCAPS, NCAPS, 2),dtype=np.double)  
                        # else:
                        #     raise Exception("Unknown roiSum_AttributeType")
                            

                    # create global big arrays to hold images
                    self.foreStack = np.zeros((numImagesF // NCAPS, NCAPS,512,512),dtype=np.double)


                    # Each time called, builds up data in data var/ roiSum.
                
                    roiSum = self.fcnToCall( self, data = roiSum, runnum = runnum)

                    if self.runVaryCommand:
                        title = f"{self.runVaryCommand} {self.varList}"

                
                #ENDFOR

                saveData(roiSum, self.pickleFilename, options = None)
                exit(0)



            elif self.bLoadFromDisk:
                # Load from Pickle file
                roiSum = loadData( self.pickleFilename)
                title =  self.fcnPlotOptions["title"] 
              

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
    vmin= -40
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

    
def loadData( fname):
    """ 
    Load data from a pickle file
    """
    filename = "DUMP.pkl" if fname is None else fname.replace(" ","_") + ".pkl" 
    with open(filename, 'rb') as f:
        data = pickle.load(f)
    print(f"Loaded data from {filename}")
    return data     



    
def saveData(data, fname, options = None):
    """ 
    Save data to a pickle file
    """
    filename = "DUMP.pkl" if fname is None else fname.replace(" ","_") + ".pkl" 

    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f"Saved data to {filename}")


#
# 
#  data is 3 dimensions: data should be [nRuns, nFrames, nCaps] 
#     options {"integ": #, "inter":#}
#
def ringWalkPlot(data, title, options:dict):
    nruns = data.shape[0]
    nframes = data.shape[1]
    ncaps = data.shape[2]
    dT = 10 # time between runs in ns

    phase = 0
    # Require  dict with these defined
    integTime = options["integ"]     
    interTime = options["inter"]     
    plt.figure(figsize=(8, 5))  # width=8 inches, height=5 inches
    
    colors = ['r', 'orange','y', 'g', 'b', 'violet', 'indigo', 'black'] 
    for c in range(ncaps):
        phase = 0
        xvalue = np.zeros(nruns)
        yvalue = np.zeros( (nruns,nframes) ) 
        for n in range(nruns):
            phase +=   dT # in ns              
       
            cphase = phase + (integTime + interTime)* c # assumes integ and inter are constant
            xvalue[n] = cphase
            ##stddev = np.std(data[n, :, c])
            #yvalue[n] = [np.mean(data[n, :, c])+stddev, np.mean(data[n, :, c])- stddev]
            yvalue[n] = data[n, :, c]
                
        #plt.plot( xvalue, yvalue,  
        #         color = colors[c], label = f"Cap {c+1}" )
        

        plt.plot(xvalue, yvalue, color=colors[c])
        # only label once
        plt.plot([], [], color=colors[c], label=f"Cap {c+1}")
            
        # endfor c
    # endfor n     

    
    plt.xlabel("Delay in (ns)")
    plt.ylabel("Mean ADU")
    plt.title(title)
    
    #plt.legend(loc='upper right', bbox_to_anchor=(1, 0.5))
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1))
   
    plt.grid()
    plt.show(block = False)    
                   
                

#
#  This version used to plot cap gain
#
def prettyPlot2(data, title, options:dict):
    nruns =  4 ## len(data)
    ncaps = len(data[0,0] )
    fig, ax = plt.subplots()
    #plt.figure(1)
    
    stdev = np.zeros(nruns,dtype=np.double)
    bestfit = np.zeros( (ncaps,2),dtype=np.double)

    
    colors = ['r', 'orange','y', 'g', 'b', 'violet', 'indigo', 'black'] 
    nframes = len(data [0])
    values = np.zeros(nframes,dtype=np.double)

    norm_diode = readCSV(options["energy_correction_filename"] )  # read in the diode values for normalization

      
    #
    ###assert len(norm_diode) == nruns, "Diode values do not match number of runs"
    #

    xrange = [1,2,3,4]
    # 4 categories
    categories = ["gain1", "gain2", "gain3", "gain4"]
    n_per_category = nframes

    normalizeValue = np.average(data[0, :, 0]) / norm_diode[0]
    for c in range(ncaps):
        for n in range(nruns):  # only first 4 runs
            
            # average the mean over all n frames
            # Divide data by the normalized diode value for that run
            values = (data[n, :, c]) / norm_diode[n] / normalizeValue
            x_positions = [n*10 + (i/nframes)*9 for i in range(nframes)]
            #stdev[n] = np.std(data[n, :, c]/ norm_diode[n] )
            #DEBUG  
            #print("DEBUG:")
            #print(    f"{data[n, :, c]}")     
            #print(f"AVE: {averageOverFrames[n]} , STDEV: {stdev[n]}")

    
            
            # label only once per capacitor (for legend)
            if n == 0:
                plt.scatter(x_positions, values, color=colors[c], label=f"Cap:{c+1}", s=15)
            else:
                plt.scatter(x_positions, values, color=colors[c], s=15)
        

        # # Create a line plot with error bars
        # ax.errorbar(
        #     xrange,
        #     averageOverFrames,
        #     yerr=stdev,
        #     color=colors[c],
        #     label=lbl,
        #     capsize=3,     # adds little caps on error bars
        #     linewidth=1.5, # optional styling
        # )

        # fit data to a line
        # store result for later
        #bestfit[c] = np.polyfit(xrange, averageOverFrames, 1)
        ##p = np.poly1d(z)
        ##print(f"Fit to line: {p}")
        ##ax.plot(xrange, p(xrange), "k--", label="Fit to line")

        # Make category ticks and labels
        plt.xticks(range(len(categories)), categories)

        plt.xlabel("Gain Category")
        plt.ylabel("Normalized Value to Gain 1.0, Cap1")
        plt.title("Values by Gain Category")
        plt.legend()
    
    # plt.xlabel( options["x_axis_label"] if options and "x_axis_label" in options else 'N' )

    # plt.ylabel('mean (ADU)')
    # plt.title( options["title"] if options and "title" in options else title)
    # ax.yaxis.set_minor_locator( MultipleLocator(1000))

     

    plt.show(block= True) 




#
# Plot <n> caps. Plot mean of ROI versus frame number
#  data is 3 dimensions: data should be [nRuns, nFrames, nCaps] 
# options is a dictionary. Currently recognizes:
#    {"x_axis_values" : [array of value]
#    {"x_axis_label" : <string> }
#    {"title" : <string> }
def prettyPlot(data, title, options:dict):
    nruns = len(data)
    ncaps = len(data[0,0] )
    fig, ax = plt.subplots()
    #plt.figure(1)
    averageOverFrames = np.zeros(nruns,dtype=np.double)
    stdev = np.zeros(nruns,dtype=np.double)
    bestfit = np.zeros( (ncaps,2),dtype=np.double)

    
    colors = ['r', 'orange','y', 'g', 'b', 'violet', 'indigo', 'black'] 
    nframes = len(data [0])

    norm_diode = readCSV(options["energy_correction_filename"] )  # read in the diode values for normalization

      
    #
    assert len(norm_diode) == nruns, "Diode values do not match number of runs"
    #

    xrange = range(nruns)
    if options and "x_axis_values" in options:
        xrange = options["x_axis_values"]  # HERE x values can get passed in here
        # options is a 1D array of floats
        pass
    for c in range(ncaps):
        for n in range(nruns):
            
            # average the mean over all n frames
            # Divide data by the normalized diode value for that run
            averageOverFrames[n] = np.average(data[n, :, c]) / norm_diode[n]
            stdev[n] = np.std(data[n, :, c]/ norm_diode[n] )
            #DEBUG  
            #print("DEBUG:")
            #print(    f"{data[n, :, c]}")     
            #print(f"AVE: {averageOverFrames[n]} , STDEV: {stdev[n]}")

        lbl = f"Cap:{c+1}"   
        


        # Create a line plot with error bars
        ax.errorbar(
            xrange,
            averageOverFrames,
            yerr=stdev,
            color=colors[c],
            label=lbl,
            capsize=3,     # adds little caps on error bars
            linewidth=1.5, # optional styling
        )

        # fit data to a line
        # store result for later
        bestfit[c] = np.polyfit(xrange, averageOverFrames, 1)
        ##p = np.poly1d(z)
        ##print(f"Fit to line: {p}")
        ##ax.plot(xrange, p(xrange), "k--", label="Fit to line")

    plt.legend()
    plt.xlabel( options["x_axis_label"] if options and "x_axis_label" in options else 'N' )

    plt.ylabel('mean (ADU)')
    plt.title( options["title"] if options and "title" in options else title)
    ax.yaxis.set_minor_locator( MultipleLocator(1000))

    
    print (bestfit) # should be 8 x [slope,offset]

    # create a residuals plot
    fig2, ax2 = plt.subplots()
    for c in range(ncaps):
        residuals = np.zeros(nruns,dtype=np.double)
        for n in range(nruns):
            residuals[n] = averageOverFrames[n] - (bestfit[c,0]*xrange[n] + bestfit[c,1])
        lbl = f"Cap:{c+1}"   
        ax2.plot( xrange,  residuals[:], 
                color=colors[c], label = lbl )  
        
    # 
    ax2.set_xlabel(options["x_axis_label"] if options and "x_axis_label" in options else "X")
    ax2.set_ylabel("Residual (ADU)")
    ax2.set_title("Residuals (Data - line fit)  per Cap")

    plt.show(block= True) 


#Wrap this code into it own function
#  # Read CSV file
#  #  # https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
def readCSV(filename):
    import pandas as pd

    # Path to your CSV file
    # This file uses the average of all the diode readings for ic0. Each Spec run starts
    # at the beginning of a run, so it roughtly matches in time
    #filename = 
    # ^ Path might break if not running From the PAD_Analysis folder


    # Read the CSV into a DataFrame
    df = pd.read_csv(filename)

    # Display the contents
    print(df) # DEBUG

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
#
#
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


    # optionally  compute the average of just the first run, and use that as the background
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
    

    #if PREVIEW_IMAGE and runnum == 0:
    if PREVIEW_IMAGE:
        zproject = np.average( dobj.foreStack, axis=0 ) # average over frames
        imagePlots( dobj, zproject, f"FmB preview {runnum+1}" )  
        plt.show(block = True)
                 

        
    
    
    for fn in range( nImages ): 
        for cn in range (ncaps):
            ave = np.average( dobj.foreStack[fn, cn, startPixY:endPixY, startPixX:endPixX] )
          
            # store ave 
            data[runnum, fn, cn] = ave
            
            

            #print( fn, cn, roiSum)

    return data







def defineListOfTests():
    """
    Create a list of (string,string) that DEFINES the 
    Take or Analyze data routines, and give each a text description
    NOTE that the string MUST match those in createObject
    """

    lot = []
    lot.append( ("Analyze_CeO2", "Linearity vs  integration time.") )
    lot.append( ("Analyze_RingWalk", "Ringwalk -  edit file to select run.") )
    lot.append( ("Ruby_integ_scan", "Linearity vs integration time w Ruby spot.") )
    lot.append( ("Ruby_gain-lin", "Linearity vs keck Gain.") )


    
    
    
    
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




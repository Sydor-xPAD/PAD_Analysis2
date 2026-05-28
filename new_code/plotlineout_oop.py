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
# v 0.4 7/31/23 OOP the S out of it. You should be able to edit createObject() to generate
#  most data runs where one thing is varied per Run and another thing is varied per frame.
# v 0.5 8/5/23 tkinter graphics
# v 0.6 8/25/23 Allow two roi's


# v 0.8 9/21/23 Allow IP differences in SRS boxes in same source
# v 0.9 12/23/23 Some fixes to SMK_021 Testing

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
# Power on
# In the command line client type:YON
#* client>YON
# Power_Control set to 1
# HV_ENABLE set to 1
# HV_OUTPUT_ENABLE set to 1
# DFPGA_DAC_OUT_VGUARD[0 - 7] set to 822.0 mV
# DFPGA_DAC_OUT_VINJ[0 - 7] set to 1644.0 mV
# DFPGA_DAC_OUT_VREF_BUF[0 - 7] set to 1233.0 mV
# DFPGA_DAC_OUT_VREF_BP[0 - 7] set to 1233.0 mV
# DFPGA_DAC_OUT_VREF[0 - 7] set to 1849.0 mV
# DFPGA_DAC_OUT_V_ISS_BUF_PIX[0 - 7] set to 719.0 mV
# DFPGA_DAC_OUT_V_ISS_AB[0 - 7] set to 668.0 mV
# DFPGA_DAC_OUT_V_ISS_BUF[0 - 7] set to 1297.0 mV
# Exposure_Mode set to 1 (One trigger for all selected caps)
# Readout_Mode set to 1 (Wait for Readout Delay)

#
# Issues with mmcmd - try this:
# mmclient -s -t &
# mmcmd open 1
#

import numpy as np
import xPadParser as BKL
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


#
# Define some globals
#
VERBOSE = 1 # 0 = quiet, 1 = print some, 2 = print a lot
#
#
# User edit settings
RAIDPATH="/mnt/raid/keckpad"

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

        self.overwrite = True  # Set to true to delete previous runs
        self.bTakeData = bTakeData
        self.bAnalyzeData = bAnalyzeData

        self.TEST_ON_MAC = False
 

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
        if self.strDescriptor == "Sweep_SRS_BurstCount":
            # Setup is using 1 VCSEL inside the integrating sphere. With 
            # Width Switch; the three rightmost switches (towards power connector) are down:
            # 1 1 1 1 1 0 0 0,  and there is one piece of silver mylar IFO the VCSEL 
            # Set HW parameters
            self.setname = 'xpad-linscan_varVREF-BP_1v5-0v5'
            self.nFrames = 30  # frames Per Run
            # SRS is setup with PER of 100us, so 30 takes 3ms
            self.integrationTime = 5000000 # 5.0 millseconds
            self.interframeTime = 1000 # 1 usec

            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0xF"       
            ]

            
            self.runVaryCommand="DFPGA_DAC_OUT_VREF_BP" 
            self.varList = [1500, 1300, 1100, 900, 700, 500] 
            self.runFrameCommand = self.usrFunction_DGCmd 
            
            self.innerVarCommand ="BURC" 
            self.innerVarList = [i for i in range(1, self.nFrames+1)]
            
            self.roi = [90, 60, 10, 10]
            self.NCAPS = 3 # can this be pulled from file?
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 3
            self.fcnPlot = prettyPlot
  
        # ****************************************************
        elif self.strDescriptor == "Sweep_Interframe1":
            # Setup is using 1 VCSEL inside the integrating sphere. With 
            # Width Switch; the three rightmost switches (towards power connector) are down:
            # 1 1 1 1 1 0 0 0,  and there is one piece of silver mylar IFO the VCSEL 
            # Set HW parameters
            self.setname = 'xpad-linscan_B100_IF1'
            self.nFrames = 20  # frames Per Run
            # SRS is setup with PER of 100us, so 20 takes 2ms
            self.integrationTime = 3000000 # 3.0 millseconds
            self.interframeTime = 100 # 100 nSec # gets swept #

            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0xF"       
            ]

            
            self.runVaryCommand="InterFrame_NSec" 
            self.varList = [200, 500, 1000, 2000, 5000, 10000] 
            self.runFrameCommand = self.usrFunction_DGCmd 

            self.innerVarCommand ="BURC" 
            self.innerVarList = [i for i in range(1, self.nFrames)]

            self.roi = [46, 92, 32, 20]
            self.NCAPS = 3 # can this be pulled from file?
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 3
            self.fcnPlot = prettyPlot

        # ****************************************************
        elif self.strDescriptor == "Sweep_Inter1":               
            # How does the slope of dark frames change as we change the interframe1 time? 
            # Set HW parameters
            #self.setname = 'xpad-scan_inter1_B27_swapBP_OR_100_100s'
            self.setname = 'xpad-scan_inter1_B27_oldRTL'
            self.nFrames = 10  # frames Per Run  
          
            # We ARE 'allowed' to change delay param in a run (!)
            
            #self.integrationTime = 50 # 100ns
            self.integrationTime = 100 # 100ns
            self.interframeTime = 100  # 100 ns - initial same on all.
            
            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0x1FF",
            ]
           
            self.runVaryCommand="Readout_Delay" 
            #self.varList = [0,50,100,150]
            self.varList = [50]
            self.runFrameCommand = self.userFunctionB
            self.innerVarList = [100,150,200,250,300, 350, 400, 450, 500, 550]
            #self.innerVarCommand ="Interframe_nsec[1]" # [0] does not work correctly BUG!
            self.innerVarCommand ="Interframe_nsec" 

            self.roi = [0, 7*16, 128, 16]
            self.NCAPS = 8 # can this be pulled from file?
            self.fcnToCall = calcEachCapLineout
            self.roiSumNumDims = 4
            self.fcnPlot = prettyAllCapsInALine

        # ****************************************************
        elif self.strDescriptor == "Sweep_w_Background":
            # Setup is using 1 VCSEL inside the integrating sphere. With 
            # Width Switch; the three rightmost switches (towards power connector) are down:
            # 1 1 1 1 1 0 0 0,  and there is one piece of silver mylar IFO the VCSEL 
            # Set HW parameters
            self.TakeBG = True
            self.MessageBeforeBackground = "Disconnect the IR strobe trigger now"
            self.MessageAfterBackground = "Plug the IR strobe trigger now"
            #self.setname = 'xpad-test1'
            self.setname = 'xpad-test2'
            self.nFrames = 25  # frames Per Run
            # SRS is setup with PER of 100us, so 20 takes 2ms
            self.integrationTime = 3000000 # 3.0 millseconds
            self.interframeTime = 200 
            
            self.varList = [200]

            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0x1FF"       
            ]

            
            self.runVaryCommand="InterFrame_NSec" 
            self.varRange = [500] 
            self.runFrameCommand = self.usrFunction_DGCmd 

            self.innerVarCommand ="BURC" 
            self.innerVarList = [i for i in range(1, self.nFrames+1)]

            self.roi = [370,88,60,16]
            self.NCAPS = 8 # can this be pulled from file?
            #self.fcnToCall = calcEachCapLineout
            self.roiSumNumDims = 4
            self.fcnPlot = prettyAllCapsInALine    



            #self.NCAPS = 3 # can this be pulled from file?
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 3
            self.fcnPlot = prettyPlot

        # ****************************************************
        elif self.strDescriptor == "Move_IR_Along_Caps":
            # Setup is using 1 VCSEL  - direct imaged. NO integrating sphere. With 
            # + Filter wheel to set intensity
            # Width Switch; 
            # 1 1 1 1 1 1 1 1, 
            # SRS Burst Mode: Off. B=A+1us.   Vary A to move pulse into each CAP exposure 
            # Set HW parameters
            self.TakeBG = True
            self.MessageBeforeBackground = "Disconnect the IR strobe trigger now"
            self.MessageAfterBackground = "Plug the IR strobe trigger now"
            #self.setname = 'xpad-test-1pulse-per-cap'
            #self.nFrames = 10  # frames Per Run
            # SRS is setup as single pulse. 
            #self.integrationTime = 100000 # 100 us
            #self.interframeTime = 500 
            self.setname = 'xpad-test-1pulse-walkthrough_500-300_20nsStep_ISS-BUFsweep2'
            self.nFrames = 100  # frames Per Run . Step 100ns steps from 700ns * 8 = 5800ns is 58 steps!
            self.integrationTime = 500 # 500ns
            self.interframeTime = 300 
            
            

            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0x0F"       
            ]

            #self.runVaryCommand="Readout_Delay"  # dummy not really scanning anything
            #self.varList = [50]
            self.runVaryCommand="DFPGA_DAC_OUT_V_ISS_BUF"  # dummy not really scanning anything
            self.varList = [1297, 800, 500]
            self.runFrameCommand = self.usrFunction_DGCmd
            # step through 500ns offset, increment A by 100.005us steps. 
            #self.innerVarList = ["{:12.6e}".format(500e-9 + i*(100e-6 + 500e-9)) for i in range(0,self.nFrames)] 
            self.innerVarList = ["{:12.6e}".format( i*(20e-9)) for i in range(0,self.nFrames)] 
            self.innerVarCommand ="DLAY 2,0,"  # Set channel A to T0 + (parameter)
 

            # ANALYZE PROPERTIES
            self.roi = [30, 71, 16, 4]
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 4

            #self.roi = [4, 0*16, 128, 16]
            self.NCAPS = 3 # can this be pulled from file?
            #self.fcnToCall = plotEachCapLineout
            #self.roiSumNumDims = 4
            #self.fcnPlot = #prettyAllCapsInALine 
            self.fcnPlot = prettyPlot
            
            # nope self.fcnPlotOptions = {"waterfall":16000}



        # ****************************************************
        elif self.strDescriptor == "Move_IR_Along_Caps_2ROIS":
            # Setup is using 1 VCSEL  - direct imaged. NO integrating sphere. With 
            # + Filter wheel to set intensity
            # Width Switch; 
            # 1 1 1 1 1 1 1 1, 
            # SRS Burst Mode: Off. B=A+1us.   Vary A to move pulse into each CAP exposure 
            # Set HW parameters
            self.TakeBG = True
            
            self.MessageBeforeBackground = "Disconnect the IR strobe trigger now"
            self.MessageAfterBackground = "Plug the IR strobe trigger now"
            #self.setname = 'xpad-test-1pulse-per-cap'
            #self.nFrames = 10  # frames Per Run
            # SRS is setup as single pulse. 
            #self.integrationTime = 100000 # 100 us
            #self.interframeTime = 500 
            self.setname = 'xp-1p-walk_2roiD'
            # frames Per Run . Step 100ns steps from 700ns * 8 = 5800ns is 58 steps!
            # 50ns steps over 800ns is 16 steps * 8 =  128
            self.nFrames = 130  
            self.integrationTime = 500 # 500ns
            self.interframeTime = 300  # was 200 
            
            

            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0x1FF"       
            ]

            self.runVaryCommand="Readout_Delay"  # dummy not really scanning anything
            self.varList = [50]
            self.runFrameCommand = self.usrFunction_DGCmd
            # step through 500ns offset, increment A by 100.005us steps. 
            #self.innerVarList = ["{:12.6e}".format(500e-9 + i*(100e-6 + 500e-9)) for i in range(0,self.nFrames)] 

            #  increment A by 100 ns steps.  700ns * 8 = 56 steps
            #self.innerVarList = ["{:12.6e}".format( i*(100e-9)) for i in range(0,self.nFrames)] 

            #  increment A by 50 ns steps.  700ns * 8 = 56 steps
            self.innerVarList = ["{:12.6e}".format( i*(50e-9)) for i in range(0,self.nFrames)] 

            self.innerVarCommand ="DLAY 2,0,"  # Set channel A to T0 + (parameter)
 

            # ANALYZE PROPERTIES
            self.roi = [396, 87, 20, 16]
            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 4

            #self.roi = [4, 0*16, 128, 16]
            self.NCAPS = 8 # can this be pulled from file?
            #self.fcnToCall = plotEachCapLineout
            #self.roiSumNumDims = 4
            #self.fcnPlot = #prettyAllCapsInALine 
            self.fcnPlot = prettyPlot
            
            # nope self.fcnPlotOptions = {"waterfall":16000}
            # define a second ROI and plot that too.
            self.roiB = [396,15,20,16] 
        # ****************************************************
        elif self.strDescriptor == "Sweep_Integ1":               
            # How does the slope of dark frames change as we change the interframe1 time? 
            # Set HW parameters
            self.setname = 'xpad-scan_integ1_B27'
            self.nFrames = 5  # frames Per Run  
          
            # We ARE 'allowed' to change delay param in a run (!)
            
            self.integrationTime = 100 # 100ns
            self.interframeTime = 100  # 100 ns - initial same on all.
            
            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0x1FF",
            ]
           
            self.runVaryCommand="Readout_Delay"
            self.varList = [0,50,100,150]
            self.runFrameCommand = self.userFunctionB
            self.innerVarList = [100,2100,6100,10100,20100]
            self.innerVarCommand ="Integration_nsec[1]" # [0] does not work correctly BUG!

            self.roi = [0, 7*16, 128, 16]
            self.NCAPS = 8 # can this be pulled from file?
            self.fcnToCall = calcEachCapLineout
            self.roiSumNumDims = 4
            self.fcnPlot = prettyAllCapsInALine    

        # ****************************************************
        elif self.strDescriptor == "Cornell_Noise":               
            self.setname = 'xpad-cornell-noise'
            self.nFrames = 100  # frames Per Run  
          
            # We ARE 'allowed' to change delay param in a run (!)
            
            self.integrationTime = 500 # 500ns
            self.interframeTime = 200  # 200 ns 
            
            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0x1FF",  # 8 CAPS
                "Trigger_Mode 2",     # HW trigger - Use External source to trigger.
                "Exposure_Mode 0"
            ]
           
            #self.runVaryCommand="Readout_Delay"
            self.varList = [1,2]   # dummy values creates two runs. use one for F one for B
            self.runFrameCommand = None
            
            self.innerVarList = []
            self.innerVarCommand = "" 

            # ANALYZE PROPERTIES
            # roi is [X,Y, W, H ]
            #self.roi = [10, 10, 118, 118] 
            self.roi = [266, 10, 108, 108] 
            self.roiB = [266+128, 10, 108, 108]
            self.NCAPS = 8 # can this be pulled from file?
            self.fcnToCall = calcBackgroundStats
            self.roiSumNumDims = 3
            self.fcnPlot = prettyPlot   
            
            self.newTitle = "Mean over ROI - Average all images"

            # Note - there are two outputs. See self.secondAnalysis
            self.fcnPlot2 = imagePlots
            self.secondTitle = "std dev of each CAP"

        
         # ****************************************************
        elif self.strDescriptor == "Cornell_Stability":               
            self.setname = 'xpad-cornell-stability'
            self.nFrames = 100  # frames Per Run  
            
            self.integrationTime = 500 # 500ns
            self.interframeTime = 200  # 200 ns 
            
            # create a list of commands to send to hardware via mmcmd 
            unique_commands = [ 
                "Cap_Select 0x1FF",  # 8 CAPS
                "Trigger_Mode 0",     # SW trigger
                "Exposure_Mode 0"
            ]
           
            #self.runVaryCommand="""
            self.varList = [100,100,100,100,100] # fill with dummy values so it runs <n> times 
            self.runFrameCommand = None
            self.innerVarList = []
            self.innerVarCommand = "" 
            #
            #
            self.delayBetweenRuns = 5  # in seconds VARY THIS to see effect of time drift
            #
            #

            # ANALYZE PROPERTIES
            self.roi = [10, 128 + 10, 108, 108]
            ###self.roiB = [128+10, 10, 108, 108]
            
            self.NCAPS = 8 # can this be pulled from file?

            self.fcnToCall = calcLinearity
            self.roiSumNumDims = 3

            self.fcnPlot = prettyPlot_TODO   
            
            self.newTitle = "Mean over ROI - Background subtracted. Using first run only"
            self.computeBackgroundFromFirstRun = True

            

        else:
             raise Exception(" !Unknown string! ") 


        # ****************************************************
        # create a list of commands to send to hardware via mmcmd 
        self.list_commands = [
            "stop",
            "Trigger_Mode 2",
            f"Image_Count {self.nFrames}",
            f"Interframe_Nsec {self.interframeTime}",
            f"Integration_Nsec {self.integrationTime}",
        ]
        self.list_commands.extend( unique_commands )
        self.list_commands.append(  f"startset {self.setname}" )



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

        # Using an SRS DG645 box:
        #IP_ADDR = "192.168.11.225"     # for keck 002
        IP_ADDR = "192.168.11.101"      # for keck002 (LLNL)
        c = comObject( 1, IP_ADDR )
        r = c.tryConnect()

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
        title = ""


        while True:
            title = ""
            runBase = 1
            backFile = None

            for runnum in range(NRUNS):
                runname = f"run_{runnum+1}"
                if self.TEST_ON_MAC: # Local Mac testing!
                    foreFile = f'/Users/yoram/Sydor/keckpad/30KV_1.5mA_40ms_f_00015001.raw' # check not sure...
                    
                else:
                    foreFile = f'/mnt/raid/keckpad/set-{setname}/run-{runname}/frames/{runname}_00000001.raw'
                
                self.fore = BKL.KeckFrame( foreFile )
                if self.TakeBG:
                    backFile = f'/mnt/raid/keckpad/set-{setname}/run-back/frames/back_00000001.raw'
                    self.back =  BKL.KeckFrame( backFile )



                numImagesF = self.fore.numImages 
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
            self.fcnPlot (roiSum, title, options = self.fcnPlotOptions)

            if hasattr(self, "roiB"):
                # repeat the analsys with a second roi
                repeat += 1  # 0 --> 1
                self.roi = self.roiB # re define the roi
                self.newTitle = "roiB"
                if repeat >= 2:
                    break
            else:
                break            
        # WHILE LOOP

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
#
def prettyPlot(data, title, options = None):
    nruns = len(data)
    ncaps = len(data[0,0] )
    fig, ax = plt.subplots()
    #plt.figure(1)
    
    nframes = len(data [0])
    for c in range(ncaps):
        for n in range(nruns):
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

            ax.plot( range(nframes), data[n,:,c], 
                color=clr )


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

    #  [ Frame, Cap, Y , X ] # TODO: check Y,X is correct
    

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
    lot.append( ("Sweep_SRS_BurstCount", "Using SRS box - adjust burst count to get linear intensity sweeps") )
    lot.append( ("Sweep_Inter1", "Adjust inteframe time [1] - see if the gradient shapes change with delay (they dont)") )
    lot.append( ("Sweep_Integ1", "Adjust integration time [1] - see if the gradient shapes change with delay (they dont)") )
    lot.append( ("Sweep_w_Background", "Sweep linearity with SRS - and also take a background") )
    lot.append( ("Move_IR_Along_Caps", "SRS single bright pulse, moves from cap1 to cap 8") )
    lot.append( ("Move_IR_Along_Caps_2ROIS", "SRS single bright pulse, moves from cap1" \
        "to cap 8. Has a bright ROI and a dark ROI.") )
    
    lot.append( ("Cornell_Noise", "Take 100 images x 8CAPS. Compute RMS from ave.") )
    lot.append( ("Cornell_Stability", "Take 1000 images x 8CAPS. Compute Mean over time. "
                  "Set self.delayBetweenRuns in units of seconds.") )
   
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




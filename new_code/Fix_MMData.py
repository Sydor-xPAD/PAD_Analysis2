#!/usr/bin/python3
#
# File: Fix_MMData.py
# History
# v 1.0 Created 13 DEC 2023
# v 1.1 updated 27APR2024 - subtract base
# v 1.2 updated 29AUG2024
# v 1.3 04JUNE2025 - Look at DESY data again
# V 1.4 12JUN2025 - Switch over to Big Keck Load 
#  Note the DESY data was WAS taken with the correct Digital Coefficients AFAICT. The config.json
# has the right values.

# Option: 'FixBadCal'
#   Loads a dataset that was taken with default 'correction values'
#  Undo, then apply the correct values. 
# INSTRUCTIONS
# Scroll down to main, and set the two variables:  examples:
#     rootDir = '/mnt/raid/mmpad/set-MMPAD_OCT2023/'
#     runName = "run-sucrose_bg"

import numpy as np

import Big_keck_load as BKL
import os
import matplotlib.pyplot as plt
import sys
from textwrap import wrap
from raw_to_mmpad import convert
VERBOSE = 2

#
#
#
def CorrectASIC(nAsic:int, dataFrame):
    # nAsic numbering
    #   3  2    1  0
    #   7  6    5  4
    #  11 10    9  8
    #  15 14   13 12

    correction_values = [ 7220, 7174, 7000, 7000,
                          7054, 7211, 7082, 6955,
                          7164, 7354, 7297, 7000,
                          6796, 7189, 7111, 7057 ]


    W = 128 
    H = 128
   # base = 7000
    cv = 16384
    sx = (3- (nAsic % 4) )* W
    sy = (nAsic // 4) * H

    #Vectorized
    # Extract the region of interest
    region = dataFrame[sy:sy+H, sx:sx+W]

    # Perform vectorized operations
    d = (region) // cv
    a = (region) - cv * d
    
    # quick sanity check
    d2 = (region & 0xFFFFC000) >> 14
    a2 = (region & 0x3FFF)
    
    if (d != d2).any():
        diff_indices = np.where(d != d2)
        print("!MISMATCH in D")
        print(diff_indices)
       
    if (a != a2).any():
        diff_indices = np.where(a != a2)
        print("!MISMATCH in A")
        print(diff_indices)
       
    if VERBOSE>= 2:
        if 1 or nAsic == 3:  # debug top left 
            positions = np.argwhere(d)
            if positions.size>0:
                print(f"ASIC#:{nAsic} Digital counts at{positions}")
            
        
    dataFrame[sy:sy+H, sx:sx+W] = a + d * correction_values[nAsic]
    #dataFrame[sy:sy+H, sx:sx+W] = d * correction_values[nAsic]
    return dataFrame

def FixBadCal( rootDir, _runName):
    PRINTDEBUGINFO = 1

    # Omit the 'run' part of the run name!
    runName = _runName[4:]

    foreFile = f"{rootDir}run-{runName}/frames/{runName}_00000001.raw"

    #foreImage = open(foreFile,"rb")
    #numImagesF = int(os.path.getsize(foreFile)/(2048+512*512*4))
    #foreStack = np.zeros((numImagesF,512,512),dtype=np.uint32)

    Fore = BKL.KeckFrame(foreFile, imgType = 'MMPAD')
    foreStack = np.zeros((Fore.numImages,512,512),dtype=np.uint32)

    
    # Load all images into one array
    for fIdex in range(Fore.numImages):
        (mdF, dataF) = Fore.getFrame()
        #(mdB, dataB) = Back.getFrame()

        print(mdF.frameNum)
        #payload = BML.mmFrame(foreImage)
        #data = payload[4]  # not super relevant for MMPAD
        dataFrame = np.resize(dataF,[512,512])
        for nAsic in range(16):
            foreStack[ fIdex, :, :] = CorrectASIC( nAsic, dataFrame) 


    # Save raw file to disk. Use a temporary file name.
    rawfilename = "temp_"+ runName + ".raw"
    foreStack.tofile(rawfilename)
    
    return rawfilename
    
    
    


    if 1:
       
        data = foreStack[0,:,:]
        fig,axis = plt.subplots(1)
        image = axis.imshow(np.log(data), cmap = "viridis")
        Acbar = fig.colorbar(image, aspect=8)

        wrappedTitle = '\n'.join(wrap(f"{foreFile}", width=60))
        axis.set_title(f"{wrappedTitle}", fontsize=8, wrap=True, loc='center')
        
        fig.tight_layout()
        axis.set_ylabel("Pixel")
        axis.set_xlabel("Pixel")
        Acbar.set_label ("Counts (ADU)")
        # fig.set_size_inches(20, 10)    
        # fig.subplots_adjust(wspace = 0.545)
        ####  plt.show()
        fig.savefig(foreFile + "[0].png")
        


if __name__ == "__main__":
    print(f"Running Fix_MMData {__name__}")
    # LINUX: rootDir = '/mnt/raid/mmpad/set-MMPAD_OCT2023/'
    #rootDir = 'c:/temp/mmpaddata/'  # Windows
    #rootDir = "\\\\sydor-fp01/Sydor Instruments Shared Data/xPAD/Data_From_DESY/set-HH_Thursday/"
    rootDir = "\\\\sydor-fp01/Sydor Instruments Shared Data/xPAD/Data_From_DESY/set-HH-Corrected_16JUNE25/"
    ## run-germanate_stills_100pct_run4\frames"
    
    
    runName = "run-germanate_stills_100pct_run4" 

    if 0:
        rawfilename = FixBadCal( rootDir, runName)
        
        outputfilename = "fixed-" + runName[4:]
        convert( rawfilename, outputfilename) # appends "00000001.raw" to filename
    
    if 0:
        runName = "germanate_stills_dark_100us_run29_00000001.raw"
        foreFile = f"{rootDir}{runName}"

        Fore = BKL.KeckFrame(foreFile, imgType = 'MMPAD')
        print(f"File:{foreFile}, {Fore.numImages}, ", end="" )
        
        (mdF, dataF) = Fore.getFrame()
        print(f"{mdF.integTime}, {mdF.interTime}")
        Fore.close()
    
        
    if 0:  ## LIST OUT the metadata for every file
        runNames = [
            #"Norun-germanate_stills_30pct_100us_run25",
            "run-germanate_stills_dark_100us_run29",
            "run-germanate_stills_40pct_run11",
            "run-germanate_stills_100pct_1000us_run18",
            "run-germanate_stills_50pct_100us_run23",
            "run-germanate_stills_100pct_100us_run17",
            "run-germanate_stills_50pct_run10",
            "run-germanate_stills_100pct_run4",
            "run-germanate_stills_60pct_100us_run22",
            "run-germanate_stills_100pct_run5",
            "run-germanate_stills_60pct_run9",
            "run-germanate_stills_10pct_100us_run27",
            "run-germanate_stills_70pct_100us_run21",
            "run-germanate_stills_10pct_run14",
            "run-germanate_stills_70pct_run8",
            "run-germanate_stills_1pct_100us_run28",
            "run-germanate_stills_80pct_100us_run20",
            "run-germanate_stills_1pct_run15",
            "run-germanate_stills_80pct_run7",
            "run-germanate_stills_1pct_run3",
            "run-germanate_stills_90pct_100us_run19",
            "run-germanate_stills_20pct_100us_run26",
            "run-germanate_stills_90pct_run6",
            "run-germanate_stills_20pct_run13",
            "run-germanate_stills_30pct_run12",
            "run-germanate_stills_dark_run16",
            "run-germanate_stills_40pct_100us_run24"
        ]
        
        
        for f in runNames:
            runName = f[4:]  # remove the 'run-'
            foreFile = f"{rootDir}run-{runName}/frames/{runName}_00000001.raw"

            Fore = BKL.KeckFrame(foreFile, imgType = 'MMPAD')
            print(f"File:{f}, {Fore.numImages}, ", end="" )
            
            (mdF, dataF) = Fore.getFrame()
            print(f"{mdF.integTime}, {mdF.interTime}")
            Fore.close()
            
    if 1:
        # Load in a corrected file    
        runName = "germanate_stills_10pct_run14"
        foreFile = f"{rootDir}run-{runName}/corrected/{runName}_00000001.raw"
        
        Fore = BKL.KeckFrame(foreFile, imgType = 'CORRECTED')
        print(f"File:{foreFile}, {Fore.numImages}, ", end="" )
        
        (mdF, dataF) = Fore.getFrame()
        print(f"{mdF.integTime}, {mdF.interTime}")
        Fore.close()
        
        dataFrame = np.resize(dataF,[612,532])
        
        fig,axis = plt.subplots(1)
        mean = 6
        stdev = 16
        
        image = axis.imshow(dataFrame[0:612,0:532], cmap = "viridis", vmin=mean-stdev, vmax=mean+stdev)
        plt.show()
        
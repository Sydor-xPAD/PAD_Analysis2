#!/usr/bin/python3
#
# File: Fix_MMData.py
# History
# v 1.0 Created 13 DEC 2023
# v 1.1 updated 27APR2024 - subtract base
# 
# Option: 'FixBadCal'
#   Loads a dataset that was taken with default 'correction values'
#  Undo, then apply the correct values. 

import numpy as np
import Big_MM_load as BML
import os
import matplotlib.pyplot as plt
import sys
from textwrap import wrap

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
    base = 7000
    cv = 16384
    sx = (3- (nAsic % 4) )* W
    sy = (nAsic // 4) * H

    # Stupid slow
    # for x in range(sx, sx+W):
    #     for y in range(sy, sy+H):
    #         v = dataFrame[y,x]
    #         d = v // cv      # digital counts
    #         a = v - cv * d   # analog residual
    #         # Apply correction
    #         dataFrame[y,x] = a + d * correction_values[nAsic ]       
    # return dataFrame

    #Vectorized
    # Extract the region of interest
    region = dataFrame[sy:sy+H, sx:sx+W]

    # Perform vectorized operations
    d = (region - base) // cv
    a = (region-base) - cv * d
    dataFrame[sy:sy+H, sx:sx+W] = a + d * correction_values[nAsic] + base
    return dataFrame

def FixBadCal():
    PRINTDEBUGINFO = 1


    rootDir = '/mnt/raid/mmpad/set-ID7B2_Oct2023/'

    # Set the run names here. Omit the 'run' part of the run name!
    runName = '720frm_sucrose_09_100pct_02'
 

    foreFile = f"{rootDir}run-{runName}/frames/{runName}_00000001.raw"

    foreImage = open(foreFile,"rb")
    numImagesF = int(os.path.getsize(foreFile)/(2048+512*512*4))
    foreStack = np.zeros((numImagesF,512,512),dtype=np.double)

    # Load all images into one array
    for fIdex in range(numImagesF):
        payload = BML.mmFrame(foreImage)
        data = payload[4]  # not super relevant for MMPAD
        dataFrame = np.resize(data,[512,512])
        for nAsic in range(16):
            foreStack[ fIdex, :, :] = CorrectASIC( nAsic, dataFrame) 


    
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
    
    FixBadCal()
   

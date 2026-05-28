#RingWalker_2.py 
# GEN II Ring walk analysis
#program to create plot of ring walk

import numpy as np
import xPadParser as BKL
import os
import matplotlib.pyplot as plt
import sys
import tkinter.filedialog as fd
import pickle as pkl
import Geo_Corr as gc
import pandas as pd


cwd = os.getcwd()


####################################
#Location of Background file for set
####################################
root_dir = '/Volumes/TOSHIBA EXT_Beige/CHESS_Nov2024/sydor_keck_data/'
backFile = root_dir + 'set-Cornell_Tests_24-11-07_RW_BG_50ns_50ns/run-back/frames/back_00000001.raw'

backImage = open(backFile,"rb")
numImagesB = int(os.path.getsize(backFile)/(1024+512*512*2))
backStack = np.zeros((8,512,512),dtype=np.double)

##################################################################################
#keckframe returns in order, returns Dict
#form keckframe[0]=frameParms
#frameParms, lengthParms, frameMeta, capNum, data, frameNum, integTime, interTime
##################################################################################

keckColumns = ["cap","data","ringPhase"]
ringWalkData = pd.DataFrame(columns=keckColumns)

#####################################
#Read in background and make AVG back
#####################################
for fIdex in range(numImagesB):
   payloadB = BKL.keckFrame(backImage)
   backStack[(payloadB[3]-1)%8,:,:] += np.resize(payloadB[4],[512,512])
avgBack = backStack/(numImagesB/8.0)

################################################
#read in all the forground files from the walk
################################################

delayStep = 29
stepSize = 10
delayStart = 110
for delay in range(delayStep):
    TD = (delay) * stepSize + delayStart
    foreStack = np.zeros((8,8,512,512),dtype=np.double)
    foreFile = "/Volumes/BMARTIN/DCS_06222022/set-HLChopper/run-scan_TD_{td}/frames/scan_TD_{td}_00000001.raw".format(td=TD)
    foreImage = open(foreFile,"rb")
    numImagesF = int(os.path.getsize(foreFile)/(1024+512*512*2))
    capTimes = np.zeros((8,8),dtype=np.double)
    absDelay = np.zeros((8),dtype=np.double)
    for fIdex in range(numImagesF):
        payloadF = BKL.keckFrame(foreImage)
        frameTime = (payloadF[6]+payloadF[7])*10
        foreStack[(payloadF[3]-1)%8,:,:] += np.resize(payloadF[4],[512,512])
        capTimes[(payloadF[3]-1)%8,:] += float(frameTime)
    avgfore = foreStack/(numImagesF/8.0)
    fmb = avgfore 
   

    
   
    avgTimes = np.mean(capTimes/(numImagesF/8.0),axis=1)
    ################################################################
    #average caps, subtract backgroubd and make absolute delay
    ################################################################


    for val in range(8):
        cap = val
        absDelay[cap] += np.sum(avgTimes[:cap])+TD
        ["cap","data","ringPhase"]
        capData = np.average(fmb[cap,0:128,0:256])
        dataclip = np.clip(capData, 0,1e3)
        df1 = pd.DataFrame({"cap":cap+1, "data":capData, "ringPhase":[absDelay[cap]]})
        ringWalkData = ringWalkData.append(df1)
# for cap in range(8):
#         maxVal = np.max(fmb[cap,:,:])
#         avgfore[cap,:,:] = fmb[cap,:,:]/maxVal
for val in range(8):
    cap = val + 1
    plotData = ringWalkData.loc[ringWalkData["cap"]==cap]
    valMax = np.max(plotData["data"])
    sdData = np.std(plotData["data"])
    meanData = np.mean(plotData["data"])
    plotData["data"] = np.clip(plotData["data"],meanData-(1*sdData),None)
    x= plotData["data"]/valMax
    y = plotData["ringPhase"]
    plt.plot(y, x,label = str(cap))
plt.legend()
plt.show()

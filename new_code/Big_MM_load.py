#created by BWM to take MM big data
#8/30/22 first creation


import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import struct


def mmFrame(dataFile):
    headerBites = dataFile.read(16)
    frameParms = struct.unpack("<HHHHII",headerBites)
    headerBites = dataFile.read(16)
    lengthParms = struct.unpack("<IHHBB6x",headerBites)
    headerBites = dataFile.read(16)
    headerBites = dataFile.read(41)
    frameMeta = struct.unpack("<QIIQIIIIB",headerBites)
    # for val in frameMeta:
    #     print(hex(val))
    frameNum = frameMeta[1]
    capNum = int(frameMeta[6]>>24)&0xf
    #print(capNum)

    dataFile.read(256-(16+16+16+41)) #read remainder of header bites

    dt = np.dtype('int32')
    data = np.fromfile(dataFile, count = (lengthParms[1] * lengthParms[2]), dtype = dt)
    dataFile.read(2048-256) #read footer bites 
    return frameParms, lengthParms, frameMeta, capNum, data, frameNum


# Frame1 = keckFrame(imageData)
# Frame2 = keckFrame(imageData)
# print(Frame2[5])
# data2d1 = np.resize(Frame1[4],[512,512])
# data2d2 = np.resize(Frame2[4],[512,512])
# fig,axs = plt.subplots(3,1)
# axs[0].imshow(data2d1)
# axs[1].imshow(data2d2)
# axs[2].imshow(data2d1-data2d2)
# plt.show()

#Frame1 = keckFrame(imageData)
# # # Frame2 = keckFrame(imageData)
#data2d1 = np.resize(Frame1[4],[512,512])
# # capAvg = np.mean(data2d1[291:364,173:240]) 
# # print(capAvg)
 # # data2d2 = np.resize(Frame2[4],[512,512])
# #  #fig,axs = plt.subplots(3,1)
#plt.imshow(data2d1[137:270,139:270])
# #     #axs[1].imshow(data2d2)
# # # axs[2].imshow(data2d1-data2d2)
#plt.show()
# Frame1 = ()

if __name__ == "__main__":

    setname="mpad-linscan1"
    runname="run_1"
    runBase = 1
    

    foreFile = r"\\sydor-fp01\Sydor Instruments Shared Data\PRODUCTS\XRAY\MMPAD\MM_Airbox_SN013\mmpad_airbox_data" + \
        fr"\set-{setname}\run-{runname}\frames\{runname}_{runBase:08d}.raw"

    #foreFile = r"\\sydor-fp01\Sydor Instruments Shared Data\PRODUCTS\XRAY\MMPAD\MM_Airbox_SN013\mmpad_airbox_data" + \
    #      r"\set-mpad-linscan1\run-run_1\frames\run_1_00000001.raw"
    
    

    imageData = open(foreFile,"rb")
    Frame1 = mmFrame(imageData)
    Frame2 = mmFrame(imageData)

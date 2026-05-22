#created by BWM to take MM big data 
#10/07/22 first creation

import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import struct

# cwd = os.getcwd()
# imageData = open(cwd +"\\PAD_Analysis2\\mm_sample.raw","rb")

def keckFrame(dataFile):

    # will need for new format Commented out for previous 
    # headerBites = dataFile.read(16)
    # frameParms = struct.unpack("<HHHHII",headerBites)
    # headerBites = dataFile.read(16)
    # lengthParms = struct.unpack("<IHHBB6x",headerBites)
    # headerBites = dataFile.read(16)
    # headerBites = dataFile.read(41)
    # frameMeta = struct.unpack("<QIIQIIIIB",headerBites)
    # # for val in frameMeta:
    # #     print(hex(val))
    # frameNum = frameMeta[1]
    # capNum = int(frameMeta[6]>>24)&0xf
    # #print(capNum)

    # dataFile.read(256-(16+16+16+41)) #read remainder of header bites

    dt = np.dtype('uint32')
    data = np.fromfile(dataFile, count = (512*512), dtype = dt)
    dataFile.read(2048) #read footer bites 
    return data

def mmFrame(dataFile):
    return keckFrame(dataFile)

# Frame1 = mmFrame(imageData)

# print(Frame1[5])
# data2d1 = np.resize(Frame1,[512,512])
# clipData = np.clip(data2d1, 0, 7e3)
# data2d2 = np.resize(Frame2[4],[512,512])
# fig,axs = plt.subplots(3,1)
# plt.imshow(clipData)
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


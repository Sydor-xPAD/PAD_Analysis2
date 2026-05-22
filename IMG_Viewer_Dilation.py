#IMG_Viewer_Dilation.py created by BWM 9/12/22
#program to create pretty averaged images plot and save them

import numpy as np
import Big_keck_load as BKL
import os
import matplotlib.pyplot as plt
import sys
import tkinter.filedialog as fd
import findpeaks.findpeaks as fp
import cv2

def file_select(Type):
  
   filename = fd.askopenfilename(
      title = "Open " + str(Type),
      initialdir = "/mnt/raid/keckpad",
  
   )
   return filename


####
#uncomment for file dialog
# backFile = file_select("Background File")
# foreFile = file_select("Foreground File")

foreFile = "/Volumes/BMARTIN/set-Geod/run-f3ms/frames/f3ms_00000001.raw"
backFile = "/Volumes/BMARTIN/set-Geod/run-b3ms/frames/b3ms_00000001.raw"
cwd = os.getcwd()
foreImage = open(foreFile,"rb")
backImage = open(backFile,"rb")
numImagesF = int(os.path.getsize(foreFile)/(1024+512*512*2))
numImagesB = int(os.path.getsize(backFile)/(1024+512*512*2))
foreStack = np.zeros((8,512,512),dtype=np.double)
backStack = np.zeros((8,512,512),dtype=np.double)
 
preview = 1 #change to 0 if dont want a preview of file
##################################
#Adjust for clipping
##################################
clipHigh = 1e4
clipLow = 50
#read all the image files
for fIdex in range(numImagesB):
   payloadB = BKL.keckFrame(backImage)
   backStack[(payloadB[3]-1)%8,:,:] += np.resize(payloadB[4],[512,512])

avgBack = backStack/(numImagesB/8.0)

for fIdex in range(numImagesF):
   payload = BKL.keckFrame(foreImage)
   foreStack[(payload[3]-1)%8,:,:] += np.resize(payload[4],[512,512])

avgFore = foreStack/(numImagesB/8.0)
plotData = avgFore-avgBack
plotDataClip = np.clip(plotData, clipLow, clipHigh)
kernel = (np.ones((3, 3), np.uint8))*1
img_erosion = cv2.erode(plotData, kernel, iterations=1)
de_noised = cv2.dilate(img_erosion, kernel, iterations=1)

 

avgplotData = np.average(de_noised, axis=0)
if preview == 1:
   avg,axs = plt.subplots(1)
   imageAvg = axs.imshow(avgplotData, cmap = "viridis")
   Acbar = avg.colorbar(imageAvg, aspect=10)
   axs.set_title('Keck Cap Average')
   axs.set_ylabel("Pixel")
   axs.set_xlabel("Pixel")
   Acbar.set_label ("Counts (ADU)")
   plt.show()
else: 
   print ("no preview")



#print(geoCalPeaks['persistance'])
#print(geoCalPeaks)
# plotData = np.resize(x, [512,512])
# plt.imshow(plotData)
# plt.show()
# dataWrite = np.savetxt(fname='peaks.txt',X=x, delimiter=' ' )
# with open('peaks.txt', 'w') as f:
#    f.write(dataWrite)
#    f.close()
# fig.set_size_inches(20, 10)    
# fig.subplots_adjust(wspace = 0.545)
#avg.savefig(foreFile + "_Avg.png")

# plt.imshow(plotData)


# allplot = []
# for val in range(8):
#    allplot.append(plotDataClip[val,:,:])


# indexVal =  (-1)
# fig,ax = plt.subplots(2,4)
# for pic in allplot:
#    indexVal += 1 
#    indexRow = int(indexVal/4) 
#    indexCol = int(indexVal%4)
#    #indexVal = allplot.index(pic)
#    image = ax[indexRow,indexCol].imshow(pic, cmap = "viridis")
#    # ax.imshow(pic)
# # fig,ax = plt.subplots(1)
# #needed to add more stuff
# # image = ax.imshow(clipData, cmap = "viridis")
#    cbar = fig.colorbar(image, aspect=10, ax = ax[indexRow,indexCol])
#    ax[indexRow,indexCol].set_title('DCS Keck Cap'+ str(indexVal))
#    ax[indexRow,indexCol].set_ylabel("Pixel")
#    ax[indexRow,indexCol].set_xlabel("Pixel")
#    cbar.set_label ("Counts (ADU)")
# fig.set_size_inches(20, 10)    
# fig.subplots_adjust(wspace = 0.545)
# #fig.savefig(foreFile + "_AvgAll.png")
# plotData1 = plotData[0,:,:]

# #average the data across all 8 caps
# plotData = np.average(plotData, axis=0)
# #clip data below to get rid of hot pixels and negative pixels
# clipData = np.clip(plotData, clipLow, clipHigh)

########################
#code to plot all 8 caps individually
########################

# plt.imshow(plotData)
# # fig,axs = plt.subplots(2,4)
# # axs[0,0].imshow(plotData[0,:,:])
# # axs[0,1].imshow(plotData[1,:,:])
# # axs[0,2].imshow(plotData[2,:,:])
# # axs[0,3].imshow(plotData[3,:,:])
# # axs[1,0].imshow(plotData[4,:,:])
# # axs[1,1].imshow(plotData[5,:,:])
# # axs[1,2].imshow(plotData[6,:,:])
# # axs[1,3].imshow(plotData[7,:,:])
# #plt.imshow(fmb[3,:,:])
# plt.show()

###################
#Code to plot and save one image with labels and such
###################

# fig,ax = plt.subplots(1)
# image = ax.imshow(clipData, cmap = "viridis")
# cbar = fig.colorbar(image, aspect=10)
# ax.set_title('DCS Keck')
# ax.set_ylabel("Pixel")
# ax.set_xlabel("Pixel")
# cbar.set_label ("Counts (ADU)")
#fig.savefig(foreFile + "_Avg.png")
#plt.show()

#################
#3d Projection plot code example
########################
# fig = plt.figure()
 
# # syntax for 3-D projection
# fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
 
# # defining all 3 axes
# z = clipData
# x = range(512)
# y = range(512)

# X, Y = np.meshgrid(x, y)

# # plotting


# surf = ax.plot_surface(X, Y, z,cmap ='viridis')
# fig.colorbar(surf, shrink=0.5, aspect=5)
# ax.set_title('DCSKeck')
# plt.show()
#############################

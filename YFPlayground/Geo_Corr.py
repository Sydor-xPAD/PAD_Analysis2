import numpy as np
import Big_keck_load as BKL
import os
import matplotlib.pyplot as plt
import sys
import tkinter.filedialog as fd

# ####file for debug####
# cwd = os.getcwd()
# foreFile = cwd +"/PAD_Anal/f3ms_00000001.raw"
# foreImage = open(foreFile,"rb")
# numImagesF = int(os.path.getsize(foreFile)/(1024+512*512*2))
# foreStack = np.zeros((numImagesF,8,612,532),dtype=np.double)
# ##################################
# #Adjust for clipping
# ##################################
# clipHigh = 1e5
# clipLow = 0

modOffSetsmm = {0:(.254,.254), 1:(1.002,.254), 2:(.254,2.922), 3:(1.002,2.922) , 4:(.254 ,6.975) , 5:(1.002 ,6.975) , 6:(.254,9.613) , 7:(1.002 ,9.613) } 

def doublePixelAdd (image):
   #############function to split charge and add 2 columns to account for double pixels in center of module######
   dPStack = np.zeros((512,516),dtype=np.double)
   indexStart = 0
   chk_Lng = 127
   indexStart2nd = 129
   indexStart2 = 2+chk_Lng*2
   indexStart3 = 2+indexStart2nd + chk_Lng*2
##########
#chunk out data into new array
##########
   dPStack[:,indexStart:indexStart+chk_Lng]+=image[:,indexStart:chk_Lng]
   dPStack[:,indexStart2nd+2:indexStart2nd+2+chk_Lng]+=image[:,indexStart2nd:indexStart2nd+chk_Lng]
  
   ####### second half #########
   dPStack[:,indexStart2+2:indexStart2+chk_Lng+2]+=image[:,indexStart2:indexStart2+chk_Lng]
   dPStack[:,indexStart3+4 :indexStart3+4+chk_Lng]+=image[:,indexStart3:indexStart3+chk_Lng]
   
   ##########splite column charge and average into 2 new columns for both half#########
   dPStack[:,indexStart+chk_Lng]+=image[:,chk_Lng]/2
   dPStack[:,indexStart+chk_Lng+1]+=image[:,chk_Lng]/2
   dPStack[:,indexStart2nd]+=image[:,indexStart2nd-1]/2
   dPStack[:,indexStart2nd+1]+=image[:,indexStart2nd-1]/2
   
   #######second half##############
   dPStack[:,indexStart2+chk_Lng+2]+=image[:,indexStart2+chk_Lng]/2
   dPStack[:,indexStart2+chk_Lng+3]+=image[:,indexStart2+chk_Lng]/2
   dPStack[:,indexStart3+2]+=image[:,indexStart3]/2
   dPStack[:,indexStart3+3]+=image[:,indexStart3]/2

   return dPStack

def GeoCor(frame):
    cordList = []
    subCount = 0 
    for pS in range (4):
        startPixY = int(pS * 128)
        for pSX in range (2):
            startPixX = int(pSX * 255)
            valuePix = np.array((startPixY,startPixX),dtype="int16")
            cordList.append(valuePix)
            #print (perAsicAvg)
            subCount +=1

    destList=[]
    for loc in range(len(modOffSetsmm)):
        destList.append(np.array(modOffSetsmm[loc])/.150 )

    GeoCorFrame = np.zeros((612,532), dtype=np.double)

    for sub in range(8):
        yVal = cordList[sub][0]
        xVal =cordList[sub][1]
        offsetx = 255
        offsety = 128
        destOSx = int(destList[sub][0]) 
        destOSy = int(destList[sub][1]) 
        GeoCorFrame[yVal+destOSy:yVal+offsety+destOSy,xVal+destOSx:xVal+offsetx+destOSx] += frame[yVal:yVal+offsety,xVal:xVal+offsetx]


                
    return GeoCorFrame

# for fIdex in range(numImagesF):
#    payload = BKL.keckFrame(foreImage)
#    resiData = np.resize(payload[4],(512,512))
#    foreStack[payload[5]-1,(payload[3]-1)%8,:,:] += GeoCor(resiData)






# plotData = np.average(foreStack,axis=0)
# plotDataClip = np.clip(plotData, clipLow, clipHigh)
# avgplotData = (np.average(plotDataClip, axis=0))
# avg,axs = plt.subplots(1)
# imageAvg = axs.imshow(avgplotData, cmap = "viridis")
# Acbar = avg.colorbar(imageAvg, aspect=10)
# axs.set_title('Average_Img')
# axs.set_ylabel("Pixel")
# axs.set_xlabel("Pixel")

# plt.show()
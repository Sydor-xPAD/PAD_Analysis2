#Filename: TBD
# Description: Generate Data for Final Report SMK 012 (LANL)
# 23 DEC 23
#
# Keywords:
#  FlatField
#  DarkCurrent


#
# Define some globals
#
VERBOSE = 1 # 0 = quiet, 1 = print some, 2 = print a lot



import numpy as np
import Big_keck_load as BKL
import os
import matplotlib.pyplot as plt
import sys
import tkinter.filedialog as fd
import pickle as pkl
##import Geo_Corr as gc
import UI_utils



def file_select(Type):
   filename = fd.askopenfilename(
      title = "Open " + str(Type),
      initialdir = "/mnt/raid/keckpad/set-HeadRework",
  
   )
   return filename


#
# 
# 
class dataObject:
   def __init__(self, strDescriptor):
      self.TEST_ON_MAC = False

      self.strDescriptor = strDescriptor
      self.rootPath = ""
      self.createObject()
      self.bClipData = False
      self.clipLow = 0
      self.clipHigh = 600
      self.bSaveFigs = True
      self.baseFileName = "FF"

   def makeData(self):
      self.FFImage = 0 # set to 0 if dont want to FF
      
      self.fgFileName = "50KV_1ms_100ns_100ims_ff_0"
      self.bgFileName = "0KV_1ms_100ns_100ims_ff_0"


      W = self.roi[2]
      H = self.roi[3]
      self.data = np.zeros((8, H, W),dtype=np.double)
      meanValue = np.zeros( (8,2), dtype=np.double)  # 8 CAPS, 2 ASICS per SM
      self.normalizedMeanValue = np.zeros( (8 * 2), dtype=np.double)  # 8 CAPS, 2 ASICS per SM
      
      kLeftSide = 0
      kRightSide = 1
      margin = 5

      aveData = self.openRunAndCreateData_DC()
      self.data = aveData
      for cap in range(8):
         meanValue[cap,kLeftSide] = np.average( aveData[cap, margin: H-(2*margin), \
            margin: int(W/2)-(2*margin) ] ) # ignore the outer (margin) pixels on edge - one ASIC at a time
      

      
         meanValue[cap,kRightSide] = np.average( aveData[cap, margin: H-(2*margin), \
            int(W/2) + margin: W- (2*margin) ] ) # ignore the outer (margin) pixels on edge - one ASIC at a time
       
      # Create a list L,R L,R L,R  for CAPS 1 to .. 8
      for cap in range(8):
         for AsicSide in range(2):
            self.normalizedMeanValue[AsicSide + 2*cap]  = meanValue[cap,AsicSide] / meanValue[0, kLeftSide]


   def makeData_DC(self):
      """
      MakeData for Dark current analysis
      Use 1 ms and a 100ns dark image data set
      """
      self.FFImage = 0 # set to 0 if dont want to FF
      #self.fgFileName = "0C_1s_dark-2"
      #self.bgFileName = "0C_100ns_dark-2"

      self.fgFileName = "0KV_1s_100ns_100ims_0"
      self.bgFileName = "0KV_100ns_100ns_100ims_0"

      W = self.roi[2]
      H = self.roi[3]
      ncaps =8
      self.data = np.zeros((ncaps, H, W),dtype=np.double)
      self.meanDarkCurrent = np.zeros( (ncaps,2), dtype=np.double)  # 8 CAPS, 2 ASICS per SM

      
      kLeftSide = 0
      kRightSide = 1
      
      margin = 32
      

      aveData = self.openRunAndCreateData_DC()
      self.data = aveData   
      for c in range(8): 
         self.meanDarkCurrent[c,kLeftSide] = np.average( aveData[c, margin: H-(2*margin), \
            margin: int(W/2)-(2*margin) ] ) # ignore the outer (margin) pixels on edge - one ASIC at a time
         self.meanDarkCurrent[c,kRightSide] = np.average( aveData[c, margin: H-(2*margin), \
            int(W/2) + margin: W- (2*margin) ] ) # ignore the outer (margin) pixels on edge - one ASIC at a time
      




   def  openRunAndCreateData( self,cap ):
      """
      Returns 2-D array, defined by ROI. Averaged over N images. F-B
      """
      #backFile = self.rootPath +  \
      #   f"\\run-{self.baseFileName}{cap}_b" +  r"\frames" + f"\\{self.baseFileName}{cap}_b_00000001.raw"
      #foreFile = self.rootPath + \
      #     f"\\run-{self.baseFileName}{cap}_f" +  r"\frames" + f"\\{self.baseFileName}{cap}_f_00000001.raw"
      
   
      backFile = self.rootPath +  \
         f"/run-{self.bgFileName}" +  r"/frames" + f"/{self.bgFileName}_00000001.raw"
      foreFile = self.rootPath + \
         f"/run-{self.fgFileName}" +  r"/frames" + f"/{self.fgFileName}_00000001.raw"



      if self.TEST_ON_MAC: # Local Mac testing!
         foreFile = f'/Users/yoram/Sydor/keckpad/30KV_1.5mA_40ms_f_00015001.raw' 
         backFile = f'/Users/yoram/Sydor/keckpad/30KV_1.5mA_40ms_f_00015001.raw' 
         

      if VERBOSE:
         print(f"backfile: {backFile};  foreFile: {foreFile}")

               
      cwd = os.getcwd()
      back = BKL.KeckFrame(backFile)
      fore = BKL.KeckFrame(foreFile)

      numImagesF = fore.numImages
      numImagesB = back.numImages

      # NOTE  - SN011 ( AKA SN020) had 1 CAP per file.  But this data set has 8 CAPS per file
      foreStack = np.zeros((8,512,512),dtype=np.double)
      backStack = np.zeros((8,512,512),dtype=np.double)
      FFStat = "noFF"
      if self.FFImage ==1 :
         fileObject = open(cwd + "/pickleFF.pi", 'rb')  # not at all tested will break 4 sure
         ffCorect = pkl.load(fileObject)
         fileObject.close()
         FFStat = "FF"
      else: 
         ffCorect = 1.0


      ##################################
      #Adjust for clipping
      ##################################
      #read all the image files
      for fIdex in range(numImagesB):
         (mdB,dataB) = back.getFrame()
         # oh oh mdb.capNum appears to be incorrect!
         cnum = fIdex % 8

         backStack[cnum,:,:] += np.resize(dataB,[512,512])
         print(".", end="")
            
      avgBack = backStack/(numImagesB/self.NCAPS_per_file)


      for fIdex in range(numImagesF):
         (mdF,dataF) = fore.getFrame()
         # oh oh mdb.capNum appears to be incorrect!
         cnum = fIdex % 8

         foreStack[cnum,:,:] += np.resize(dataF,[512,512])
         print(".", end="")

      avgFore = foreStack/(numImagesF/self.NCAPS_per_file)

      if self.TEST_ON_MAC:
         plotData = (avgFore) * ffCorect

      else:
         plotData = (avgFore-avgBack) * ffCorect

      if self.bClipData:
         plotData = np.clip(plotData, self.clipLow, self.clipHigh)
      ###tavgplotData = gc.GeoCor(np.average(plotData, axis=0))
      
      ###tavgplotData = np.average(plotData, axis=0)
      
      
      # rio is [X,Y,W,H]
      startPixY = self.roi[1]
      endPixY = startPixY + self.roi[3]
      startPixX = self.roi[0]
      endPixX = startPixX + self.roi[2]
      result =  plotData[ 0,  startPixY:endPixY, startPixX:endPixX ]
      return result


   def  openRunAndCreateData_DC( self ):
      """
      For Dark Current analysis. Returns average over N of F-B as a data_array[caps, W, H] 
      """
      backFile = self.rootPath +  \
         f"/run-{self.bgFileName}" +  r"/frames" + f"/{self.bgFileName}_00000001.raw"
      foreFile = self.rootPath + \
         f"/run-{self.fgFileName}" +  r"/frames" + f"/{self.fgFileName}_00000001.raw"
      

      if self.TEST_ON_MAC: # Local Mac testing!
         foreFile = f'/Users/yoram/Sydor/keckpad/30KV_1.5mA_40ms_f_00015001.raw' 
         backFile = f'/Users/yoram/Sydor/keckpad/30KV_1.5mA_40ms_f_00015001.raw' 
         

      if VERBOSE:
         print(f"backfile: {backFile};  foreFile: {foreFile}")

               
      cwd = os.getcwd()
      back = BKL.KeckFrame(backFile)
      fore = BKL.KeckFrame(foreFile)

      numImagesF = fore.numImages
      numImagesB = back.numImages


      foreStack = np.zeros((8,512,512),dtype=np.double)
      backStack = np.zeros((8,512,512),dtype=np.double)
      FFStat = "noFF"
      if self.FFImage ==1 :
         fileObject = open(cwd + "/pickleFF.pi", 'rb')  # not at all tested will break 4 sure
         ffCorect = pkl.load(fileObject)
         fileObject.close()
         FFStat = "FF"
      else: 
         ffCorect = 1.0


      ##################################
      #Adjust for clipping
      ##################################
      #read all the image files
      for fIdex in range(numImagesB):
         (mdB,dataB) = back.getFrame()
         # oh oh mdb.capNum appears to be incorrect!
         cnum = fIdex % 8
         backStack[cnum,:,:] += np.resize(dataB,[512,512])
         print(f"{cnum}", end="")
            
            
      avgBack = backStack/(numImagesB/self.NCAPS_per_file)
      
      for fIdex in range(numImagesF):
         (mdF,dataF) = fore.getFrame()
         # oh oh mdb.capNum appears to be incorrect!
         cnum = fIdex % 8
         foreStack[cnum,:,:] += np.resize(dataF,[512,512])
         print(f"{cnum}", end="")

      avgFore = foreStack/(numImagesF/self.NCAPS_per_file)

      if self.TEST_ON_MAC:
         plotData = (avgFore) * ffCorect

      else:
         plotData = (avgFore-avgBack) * ffCorect

      
      # ROI is [X,Y,W,H]
      startPixY = self.roi[1]
      endPixY = startPixY + self.roi[3]
      startPixX = self.roi[0]
      endPixX = startPixX + self.roi[2]
      result =  plotData[ :, startPixY:endPixY, startPixX:endPixX ]
      return result


   def makePlot(self):
      """
      self.data should be [N,H,W], where N = # CAPS.
      Generate a 4 x 2 grid of flatfield images - one for each Cap.
      """
      allplot = []
      dim0 = self.data.shape[0] 
      for val in range(dim0):
         #allplot.append(gc.GeoCor(self.data[val,:,:]))
         allplot.append(self.data[val,:,:])


      indexVal =  (-1)
      fig,ax = plt.subplots(2,4,sharex='col', sharey='row')

      for pic in allplot:
         indexVal += 1 
         indexRow = int(indexVal/4) 
         indexCol = int(indexVal%4)
         #indexVal = allplot.index(pic)
         image = ax[indexRow,indexCol].imshow(pic, cmap = "viridis")
         # ax.imshow(pic)
         # fig,ax = plt.subplots(1)
         #needed to add more stuff
         # image = ax.imshow(clipData, cmap = "viridis")
         mean = np.mean(pic)
         stdev = np.std(pic)
         image.set_clim(vmin= mean - stdev, vmax = mean+stdev)

         cbar = fig.colorbar(image, aspect=4, ax = ax[indexRow,indexCol] )
         ax[indexRow,indexCol].set_title('Keck Cap'+ str(1+ indexVal))
         if indexCol == 0:
            ax[indexRow,indexCol].set_ylabel("Pixel")
         if indexRow == 1:   
            ax[indexRow,indexCol].set_xlabel("Pixel")
         cbar.set_label ("Counts (ADU)")
         


      fig.set_size_inches(12, 4)    
      fig.subplots_adjust(wspace = 0.645, hspace = -0.2) # space is padding height
      plt.tight_layout()

    

      if self.bSaveFigs:
         fig.savefig(self.baseFileName + "_AvgAll.png")
      

      # PLOT TWO
      #
      #
      ###################
      #Code to plot and save one image with labels and such
      ###################

      fig,ax = plt.subplots(1)
      
      plt.ylabel('Normalized to Left ASIC, CAP1')
      catNames = [f"Cap{c+1}" for c in range(8)]
      X = 1 + np.arange(8)
      bar_width = 0.4
      ax.bar(X - bar_width/2, [self.normalizedMeanValue[s]-1 for s in range(0,16,2)], color = 'b', width=bar_width )
      ax.bar(X + bar_width/2, [self.normalizedMeanValue[s]-1 for s in range(1,16,2)], color = 'r', width=bar_width )
      ax.legend(labels=['Left', 'Right'])
      ###ax.set_xticklabels( catNames )
      ###ax.set_yticklabels( [ '.8','.9', '1.0', '1.1', '1.2'] )
      ###ax.set_ylim(-.2, 0.2)
      nt = np.arange(-2,3,1)
      amp = .010
      ax.set_yticks(nt* amp ,  list(map(str, 1 + nt * amp)))
      ax.set_xticks([1,2,3,4,5,6,7,8,9],   catNames +[""])


      plt.title( 'Compare Flatfield of each CAP' )
      plt.ylabel('Counts')


      if self.bSaveFigs:
         fig.savefig(self.baseFileName + "_RelGain_barchart.png")


   def makePlot_DC(self):
      """
      self.data should be [N,H,W], where N = # CAPS.
      Generate a plot of dark current for each of the 8 CAPS
      """
      
      fig,ax = plt.subplots(1)
      
      ax.plot(np.arange(16), np.resize(self.meanDarkCurrent / 1000,[16,1]))
      plt.ylabel('Counts')
      plt.xlabel('Left & Right for each CAP')
      plt.title( 'Dark Current (Counts / ms )')
      
      catNames = []
      for c in range(8):
         catNames.append( f"Cap{c+1}" )
         #catNames.append( f"R_Cap{c+1}" )

      ax.set_xticks(0.5 + np.arange(8)*2,   catNames )



      if self.bSaveFigs:
         fig.savefig(self.fgFileName + ".png")
      

      

   def createObject(self):
      # ****************************************************
      if self.strDescriptor == "Flatfield":            
         # with geo self.roi = [262, 144, 256+1, 128]
         self.roi = [256, 0, 256, 128]
         self.NCAPS_per_file = 8 
         self.fcnToCall = self.makeData
         self.fcnPlot   =  self.makePlot
         #self.rootPath = r"Z:\PRODUCTS\XRAY\KeckPAD\SMKeck_012_CdTe_LANL\Data\keckpad_sn012_dec2023\set-22DEC2023"
         self.rootPath = r"D:\github"


      elif self.strDescriptor == "DarkCurrent":  
         
         self.rootPath = r"/mnt/raid/keckpad/set-xpad-cornell-noise"
         self.rootPath = r"Z:\PRODUCTS\XRAY\KeckPAD\SMKeck_012_CdTe_LANL\Data\keckpad_sn012_dec2023\set-22DEC2023"  # \run-0KV_1s_100ns_100ims_0"
         self.roi = [256, 0, 256, 128]          
         self.NCAPS_per_file = 8 
         self.fcnToCall = self.makeData_DC
         self.fcnPlot   =  self.makePlot_DC
         


      else:
         raise Exception(" !Unknown string! ")    
      

  
   #
   # 
   #         
   def Analyze_Data(self):
      """
      Load up the runs, and analyze
      """
      self.fcnToCall()
      self.fcnPlot()






if 0:
   
   
   
   avg,axs = plt.subplots(1)
   imageAvg = axs.imshow(avgplotData, cmap = "viridis")
   Acbar = avg.colorbar(imageAvg, aspect=10)
   axs.set_title('Keck Cap Average')
   axs.set_ylabel("Pixel")
   axs.set_xlabel("Pixel")
   Acbar.set_label ("Counts (ADU)")
   # fig.set_size_inches(20, 10)    
   # fig.subplots_adjust(wspace = 0.545)
   avg.savefig(foreFile + FFStat +"_Avg.png")

   # plt.imshow(plotData)


   
   #average the data across all 8 caps
   plotData = np.average(plotData, axis=0)
   #clip data below to get rid of hot pixels and negative pixels
   clipData = np.clip(plotData, clipLow, clipHigh)

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
   plt.show()

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


   plt.show()





def defineListOfTests():
    """
    Create a list of (string,string) that DEFINES the 
    Analyze data routines, and give each a text description
    NOTE that the string MUST match those in createObject
    """

    lot = []
    lot.append( ("Flatfield","Analyze the 8 FF files. ") )
    lot.append( ("DarkCurrent","Analyze dark long exposure minus dark short exposure. ") )
    # TODO - add more here
    # TODO - need to add noise here is two short images subtracted f e o.
    return lot


# INSTRUCTIONS
# Run plotlineout_oop.py
# Select Dark_cURRENT ,doesn exit yuet>.
# make sure HW triggers aere setup
#    it will save run1 and run2. they are identical. use one as F and one as B.


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
   dobj = dataObject( strDescriptor)

   ret = dobj.Analyze_Data()
   plt.show()

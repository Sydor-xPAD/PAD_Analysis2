#Filename: Debounce.py
# Description: Given an F and B image runs,
#  Debounce the data using some fancy heuristic
#
#
# Keywords:
# Debounce

#
# Define some globals
#
VERBOSE = 1 # 0 = quiet, 1 = print some, 2 = print a lot
INTERACTIVE_MODE = 1   # 1 = Use terminal input and UI buttons to
                       #  cycle through each frame and ASIC one-at-a-time



import numpy as np
import Big_keck_load as BKL
import os
import matplotlib.pyplot as plt
import sys
import tkinter.filedialog as fd
import pickle as pkl
##import Geo_Corr as gc
import UI_utils
from matplotlib.widgets import Button

from scipy.signal import find_peaks  # Peak finding


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
      self.TEST_ON_MAC = True

      self.strDescriptor = strDescriptor
      self.rootPath = r"Z:\Project#_1300_1499\#1415 SM HE Keck CdTe LANL\set-SMK020FTR"
      if self.TEST_ON_MAC:
         self.rootPath = "/Users/yoram/Sydor/MM-PAD_Data/"

      self.createObject()
      self.nASIC = 0
      self.fIdex = 0
      self.bClipData = False
      self.margin = 5     ## How many pixels to shrink in the ROI on each ASIC
      self.bSaveFigs = True
      self.nCAPS = 1 # MMPAD is 1
      self.readRAW = 1  ## RAW data = has already been processed and contains
                        # no header or footer

      self.numImagesF = 1000
      self.numImagesB = 1000
      self.numBins = 200
      self.histogramBinStart = -200
      self.histogramBinEnd = 800
      self.skipBackFrames = [ 0 ]  # A list of frames (0-based) to skip

      # scipy peak finding parameters 
      self.fpHeight = 50
      self.fpWidth = (3,10)

      self.backFile = self.rootPath + f"sucrose_bg.raw"
      ##self.foreFile = self.rootPath + f"sucrose_1pt.raw"
      self.foreFile = self.rootPath + f"output.raw"
     
   def doCorrelarion(self):
      pass


   def doDebounce(self):
      debounceMatrix = np.zeros( (self.numImagesF, 16), dtype = np.dtype('double')) 
      W = 128 
      H = 128
      with open('debounce_vals.txt', 'r') as file:
         for line in file:
            if line.startswith('#'):
               continue

            tokens = line.strip().split(',')
            debounceMatrix[ int(tokens[1]), int(tokens[2]) ] = float(tokens[3])

      foreStack = np.zeros((self.numImagesF,512,512),dtype=np.int32)
      if self.readRAW:
         f = open( self.foreFile,"rb")
         # Subtract average background, put in 'fore'
         for fIdex in range(self.numImagesF):
            dataF = np.fromfile(f, count = (512 * 512), dtype = np.dtype('int32'))
            # Advance the file pointer
            foreStack[fIdex,:,:] = np.resize(dataF,[512,512]) 

         f.close() 

      # Subtract it out
      for fIdex in range(self.numImagesF):
         for nAsic in range(16):
            # rio is [X,Y,W,H]
            startPixX = (nAsic % 4)* W 
            endPixX = startPixX + W 

            startPixY = (nAsic // 4)*H
            endPixY = startPixY + H 

            subRegion = foreStack[ fIdex,  startPixY:endPixY, startPixX:endPixX ] - int(round(debounceMatrix[fIdex, nAsic]))
            foreStack[ fIdex,  startPixY:endPixY, startPixX:endPixX ] = subRegion          
                  
      # Write it out
      foreStack.tofile('output.raw');
            

   def makeData(self):
      self.FFImage = 0 # set to 0 if dont want to FF
      self.baseFileName = "" # not relevant
     
      # Returns a [nAsic, frame#]  or 16 x 1000 array
      self.meanArray, self.histArray = self.openRunAndCreateData()

      ## Save arrays to disk using pickle
      #print("*** Saving data to data.pkl")

      #with open('data.pkl', 'wb') as file:
      #   pkl.dump(self.foreStack, file)

     

        

   def  openRunAndCreateData( self):
      """
      Returns mean of each ASIC of F-B
      Also sets self.foreData[]
      """
      W = 128 
      H = 128

      backFile = self.backFile
      foreFile = self.foreFile
               

      if VERBOSE:
         print(f"backfile: {backFile};  foreFile: {foreFile}")

      actualNumImagesB = 0        
      cwd = os.getcwd()

      if self.readRAW:
         numImagesF = self.numImagesF
         numImagesB = self.numImagesB
         foreStack = np.zeros((numImagesF,512,512),dtype=np.double)
         backStack = np.zeros((512,512),dtype=np.double)
         
         f = open( backFile,"rb")
         #read all the image files
         for fIdex in range(numImagesB):
            if fIdex in self.skipBackFrames:
               continue 
            dataB = np.fromfile(f, count = (512 * 512), dtype = np.dtype('int32'))
            backStack[:,:] += np.resize(dataB,[512,512])
            actualNumImagesB += 1
         f.close()


      else:
        back = BKL.KeckFrame(backFile, imgType = 'MMPAD')
        fore = BKL.KeckFrame(foreFile, imgType = 'MMPAD')

        numImagesF = fore.numImages
        numImagesB = back.numImages


        foreStack = np.zeros((numImagesF,512,512),dtype=np.double)
        backStack = np.zeros((512,512),dtype=np.double)
        
        actualNumImagesB = 0
        
        #read all the image files
        for fIdex in range(numImagesB):
            if fIdex in self.skipBackFrames:
               continue 
            (mdB,dataB) = back.getFrame()
            backStack[:,:] += np.resize(dataB,[512,512])
            actualNumImagesB += 1


     # ##########################       
      avgBack = backStack / actualNumImagesB
      
      if self.readRAW:
         f = open( foreFile,"rb")
         # Subtract average background, put in 'fore'
         for fIdex in range(numImagesF):
            dataF = np.fromfile(f, count = (512 * 512), dtype = np.dtype('int32'))
            # Advance the file pointer
            foreStack[fIdex,:,:] = np.resize(dataF,[512,512]) - avgBack

         f.close()

    
      # store the FmB data in object
      self.foreStack = foreStack

      # Plot the first one for a reality check.
      ###plotData = foreStack[700,:,:]  # skip 0,1,2   They are not so good.
      ###plt.imshow(plotData, cmap='viridis')  
      ###plt.title( "Sample Image of F m B" )

      NUM_BINS =  self.numBins
      meanArray = np.zeros((16,numImagesF),dtype=np.double)
      histArray = np.zeros((16,numImagesF, NUM_BINS),dtype=np.double)

      for fIdex in range(numImagesF):
        for nAsic in range(16):
            # rio is [X,Y,W,H]
            startPixX = (nAsic % 4)*W + self.margin 
            endPixX = startPixX + W - (self.margin*2)

            startPixY = (nAsic // 4)*H + self.margin
            endPixY = startPixY + H - (self.margin*2)
            subRegion = foreStack[ fIdex,  startPixY:endPixY, startPixX:endPixX ]
            meanArray[nAsic, fIdex] =  subRegion.mean()

            # Will this create an array for each nAsic, fIdex?
             # Calculate histogram
            hist, bin_edges = np.histogram(subRegion, bins=NUM_BINS, 
               range=(self.histogramBinStart, self.histogramBinEnd) )
            histArray[nAsic, fIdex, :] = hist
            # check size of hist is NUM_BINS
      
      return meanArray, histArray

   #
   #
   #
   def update_histogram(self, fig, ax, inc_dir=0):
       # Plot some histograms     

     

      if inc_dir == 1:
         self.nASIC += 1
         if self.nASIC > 15:
            self.nASIC = 0
            self.fIdex += 1

      elif  inc_dir == -1:
         self.nASIC -= 1
         if self.nASIC < 0:
            self.nASIC =15
            self.fIdex -= 1


      if self.fIdex <0:
         self.fIdex = 0
      if self.fIdex > self.numImagesF:
         self.fIdex = self.numImagesF 


      if not hasattr(self, 'histogram'):
         self.histogram,  =  ax.plot( 
            np.arange( 
               self.histogramBinStart, 
               self.histogramBinEnd, 
               (self.histogramBinEnd-self.histogramBinStart) / self.numBins
            ), 
            self.histArray[self.nASIC, self.fIdex,:] , 
            marker='o', markersize=3 )


         plt.show(block=False)  # Show the plot without blocking

      else:      
                                
         self.histogram.set_ydata( self.histArray[self.nASIC, self.fIdex,:])
      

      # Set the y-axis limits
      ax.autoscale_view(True, True, True)

     
      ##ax.set_ylim(-100, 200)

      fig.suptitle(f"Frame: {self.fIdex}, ASIC {self.nASIC}")


      # Next Peak Finding
      ipeaks, xpeaks, ypeaks = self.findPeaks()  
      if hasattr(self, "second_markers"):
         self.second_markers.remove()
      # plot the found peaks over the graph
      self.second_markers = ax.scatter( xpeaks, ypeaks, color='r')

      fig.canvas.draw()
      fig.canvas.flush_events()   


      # The criteria
      if len(ipeaks)>= 2:
         if  -150 < xpeaks[0] < 150:  # You can do this in Python!
            print( f"*** Frame:{self.fIdex} ASIC:{self.nASIC} Subtract:{xpeaks[0]}")
     
   

   #
   #
   #   
   def findPeaks(self):
      """
      Start at 'left'. Find atleast two peaks that meet criteria
      """   
      lineout = self.histArray[self.nASIC, self.fIdex,:] 


      # Find peaks with height __,  and width between _and _ samples
      peaks, _ = find_peaks(lineout, height=self.fpHeight, width=self.fpWidth)


      xpeaks = [int(self.histogramBinStart + 
                  peak * (self.histogramBinEnd - self.histogramBinStart) / self.numBins)
                  for peak in peaks]
      
      #if VERBOSE:
      #   print(peaks, xpeaks)

      return peaks, xpeaks, lineout[ peaks ]     



   def update_plot(self, fig, ax, fIdex):
      NASICS = 16

      # Create a colormap object
      cmap = plt.get_cmap('viridis')  # You can choose any colormap you like


     
      ax.relim()

     

      allplot = []
      for val in range( NASICS):      
         # put two identical values per, so can show as line segments  
         allplot.append(self.meanArray[val,fIdex])
         allplot.append(self.meanArray[val,fIdex])

      # Get a color from the colormap based on the index
      color = cmap(fIdex / (self.numImagesF - 1))  # Normalize the index to [0, 1] range   

      if not hasattr(self, 'line'):
         ranges = []
         step = 1
         for n in range(0, 16):
            start = n - 0.5
            stop = n + 0.5            
            ranges.append(start)
            ranges.append(stop)
         ##ranges = np.array(ranges)   
         self.line,  = ax.plot( ranges, allplot )
         plt.show(block=False)  # Show the plot without blocking

      else:                                      
         self.line.set_ydata( allplot)
      

      # Set the y-axis limits
      ax.autoscale_view(True, True, True)
      fig.canvas.draw()
      fig.canvas.flush_events()   
      ax.set_ylim(-100, 200)
      fig.suptitle(f" Frame: {fIdex}")
   

     


   def split_string_to_ints(self, string, default_values=('0', '0', '0')):
      values = string.split(',')
      value1, value2, value3 = (values + list(default_values))[:3]
      return int(value1), int(value2), int(value3)

   def plotCorrelation(self):
      dim0 = self.meanArray.shape[0]  # # frames
      dim1 = self.meanArray.shape[1]  # # asics

      fig, axes = plt.subplots(nrows=1, ncols=4, figsize=(16, 4))

      # Ask for user input and update the plot
      if INTERACTIVE_MODE:
         while True:
            user_input = input("Enter frame A1,A2  (or 'q' to quit): ")
            if user_input.lower() == 'q':
               break
            try:
               a1, a2, _ = self.split_string_to_ints(user_input)
               
               # TODO
               # Plot data in each figure
               for i,ax in enumerate(axes.flat):
                  ax.cla()
                  if a2+i > 15:
                     break
                  ax.plot(self.meanArray[a1, :], self.meanArray[a2+i, :], 
                          label=f'Figure {i+1}')
                  ax.set_title(f'Figure {a1} vs {a2+i}')


               for ax in axes.flat:
                  ax.set_xlim(-150, 300)  
                  ax.set_ylim(-150, 300)  
               

               fig.suptitle(f"ASICs: {a1} vs {a2} +0, +1, +2, +3")
               # Redraw the canvas
               fig.canvas.draw()
               fig.canvas.flush_events()
               plt.show(block=False)  # Show the plot without blocking
               
            except ValueError:
               print("Invalid input. Please enter a number or 'q' to quit.")

      else:
         # Compute the correlation coefficient matrix
         asicA = 4
         for i in  range(16):
            arr1 = self.meanArray[asicA, :]
            arr2 = self.meanArray[i, :]

            # Filter out values outside the range -200 to +200
            mask1 = np.logical_and(arr1 >= -200, arr1 <= 200)
            mask2 = np.logical_and(arr2 >= -200, arr2 <= 200)
            mask = np.logical_and( mask1, mask2)


            # Apply the masks to the arrays
            filtered_array1 = arr1[mask]
            filtered_array2 = arr2[mask]
            correlation_matrix = np.corrcoef(filtered_array1, filtered_array2)

            # Extract the correlation coefficient
            correlation_coefficient = correlation_matrix[0, 1]
            print( f"A:{asicA} vs A:{i}, {round(correlation_coefficient,4)}" ) 

   def makePlot(self):
      """
      self.data should be [nAsic, NFrames], 
        where nAsic = 16  (the number of ASICS per image)
        and NFrames = ~1000, the number of frames in the dataset
      Plot the 16 averages along one line, repeat for each frame
      """
      
      dim0 = self.meanArray.shape[0] 
      dim1 = self.meanArray.shape[1]

      fig, ax = plt.subplots()
      
      ax.set_xlabel('ASIC#')
      ax.set_ylabel('Mean')

      fig2, ax2 = plt.subplots()
      ## plt.title(f" Frame: {self.fIdex}, ASIC {self.nASIC}")

      
      # Create the "Prev" button
      prev_button_ax = plt.axes([0.1, 0.9, 0.1, 0.075])
      prev_button = Button(prev_button_ax, 'Prev')

      # Create the "Next" button
      next_button_ax = plt.axes([0.8, 0.9, 0.1, 0.075])
      next_button = Button(next_button_ax, 'Next')

      prev_button.on_clicked( lambda event: self.update_histogram(fig2, ax2, inc_dir=-1))      
      next_button.on_clicked( lambda event: self.update_histogram(fig2, ax2, inc_dir=1))


      self.update_plot(fig, ax, self.fIdex)
      self.update_histogram(fig2, ax2)


      # Ask for user input and update the plot
      if INTERACTIVE_MODE:
         while True:
            user_input = input("Enter frame #  (or 'q' to quit): ")
            if user_input.lower() == 'q':
               break
            try:
               self.fIdex = int(user_input)
               
               self.update_plot(fig, ax, self.fIdex)
               self.update_histogram(fig2, ax2)
               
            except ValueError:
               print("Invalid input. Please enter a number or 'q' to quit.")

      else:
         with open('debounce_vals.txt', 'w') as file:
    
            for fIdex in range(self.numImagesF):
               for nASIC in range(16):
                  self.fIdex = fIdex
                  self.nASIC = nASIC
                  ipeaks, xpeaks, ypeaks  = self.findPeaks()

                  # The criteria
                  if len(ipeaks)>= 2:
                     if  -150 < xpeaks[0] < 150:  # You can do this in Python!
                        print( f"*** Frame:{self.fIdex} ASIC:{self.nASIC} Subtract:{xpeaks[0]}")
                        file.write(f"1,{self.fIdex},{self.nASIC},{xpeaks[0]}\n")
                     else:
                        file.write(f"-1,{self.fIdex},{self.nASIC}, 0 \n")
                  else:
                     file.write(f"-2,{self.fIdex},{self.nASIC}, 0 \n")      


   

   def createObject(self):
      # ****************************************************
      if self.strDescriptor == "1-GetBounce":            
         self.margin = 5  # Shrink in x pixels from each side on the ASIC ROI
         self.NCAPS_per_file = 1 
         self.fcnToCall = self.makeData
         self.fcnPlot   =  self.makePlot


      elif self.strDescriptor == "2-DoCorrection":            
         self.fcnToCall = self.doDebounce
         self.fcnPlot   =  None

      elif self.strDescriptor == "3-Correlations":   
         self.corr = (4,5)         
         self.fcnToCall = self.makeData
         self.fcnPlot   =  self.plotCorrelation   
     


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
      if self.fcnPlot:
         self.fcnPlot()







def defineListOfTests():
    """
    Create a list of (string,string) that DEFINES the 
    Analyze data routines, and give each a text description
    NOTE that the string MUST match those in createObject
    """

    lot = []
    lot.append( ("1-GetBounce","Run once. Will generate text file of debounces") )
    lot.append( ("2-DoCorrection","Applies debounce corrections and saves new data.") )
    lot.append( ("3-Correlations", "Look at correlations of means between two ASICs") )
    # TODO - add more here
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
   dobj = dataObject( strDescriptor)

   ret = dobj.Analyze_Data()
   plt.show()

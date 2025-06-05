#MM_PAD_Viewer.py 
#program to load and view the direct images on RAID drive
# 
# v 0.1 YF 10/20/23
# Look at Cornell data taken at S7 on Oct 2023

import numpy as np
import Big_MM_load as BML
import os
import matplotlib.pyplot as plt
import sys
from textwrap import wrap


def file_select(Type):
  
   filename = fd.askopenfilename(
      title = "Open " + str(Type),
      ##########
      #Change location so you dont need to click so much
      ##########
      initialdir = "/mnt/raid/mmpad/set-ID7B2_Oct2023",
  
   )
   return filename

if __name__ == "__main__":
    PRINTDEBUGINFO = 1

    rootDir = '/mnt/raid/mmpad/set-ID7B2_Oct2023/'
    
    # Set the run names here. Omit the 'run' part of the run name!
    runNameF = '720frm_sucrose_09_100pct_02'
    runNameB = '720frm_sucrose_09_100pct_02'


    foreFile = f"{rootDir}run-{runNameF}/frames/{runNameF}_00000001.raw"
    backFile = f"{rootDir}run-{runNameB}/frames/{runNameB}_00000001.raw"
    
    cwd = os.getcwd()
    
    foreImage = open(foreFile,"rb")
    backImage = open(backFile,"rb")
    numImagesF = int(os.path.getsize(foreFile)/(2048+512*512*4))
    numImagesB = int(os.path.getsize(backFile)/(2048+512*512*4))
    foreStack = np.zeros((512,512),dtype=np.double)
    backStack = np.zeros((512,512),dtype=np.double)


    for fIdex in range(numImagesF):
        payload = BML.mmFrame(foreImage)
        data = payload[4]  # not super relevant for MMPAD
        foreStack[:,:] += np.resize(data,[512,512])

        if PRINTDEBUGINFO:
            print(f"F#:{fIdex}  frameParms:{payload[0]}, lengthParms:{payload[1]}, "
                f"frameMeta:{payload[2]}, capNum:{payload[3]}, frameNum:{payload[5]}")

        if fIdex == 25:
            pass # breakpoint here


    # skip background subtraction   
    avgFore = foreStack/(numImagesF)     
    plotData = avgFore


    avg,axs = plt.subplots(1)
    imageAvg = axs.imshow(np.log(plotData), cmap = "viridis")
    Acbar = avg.colorbar(imageAvg, aspect=8)

    wrappedTitle = '\n'.join(wrap(f"{foreFile}", width=60))
    axs.set_title(f"{wrappedTitle}", fontsize=8, wrap=True, loc='center')
    
    avg.tight_layout()
    axs.set_ylabel("Pixel")
    axs.set_xlabel("Pixel")
    Acbar.set_label ("Counts (ADU)")
    # fig.set_size_inches(20, 10)    
    # fig.subplots_adjust(wspace = 0.545)
    plt.show()
    ##avg.savefig(foreFile + FFStat +"_Avg.png")


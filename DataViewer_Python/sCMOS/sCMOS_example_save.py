#!/usr/bin/python

#File sCMOS_example_save.py
# Simple example to connect to the DataViewer socket and setup the sCMOS (Wraith)
# Camera and save data to file.
# History
# Ver 1.0 YF 20FEB2024
# Ver 1.1 YF 01MAR2024


import sys
import time
import DV_socket

epics_cmd_port = 10030
DV_Address = "127.0.0.1"   # use 127.0.0.1 for local host

# GLOBALS
N_IMAGES = 80
# Checked at 40.
# Checked at 80.

INTERFRAME_TIME_MS = 10

# start the program         
def main(argv):
    
    dvs = DV_socket.DataViewerSocket(DV_Address)
    
    # 0 = Live
    # 1 = Capture to RAM
    # 2 = Capture to File
    dvs.set('CaptureMode', 2) 
    
    # # of images
    dvs.set('NImages', N_IMAGES) 
   
    # software trigger (0), external trigger (3) 
    dvs.set("Trigger", 0)
   
    # what gain are you using? "high" or "low" ? 
    gain = "high" 
   
    # Set Interframetime if set
    dvs.set("Interframe",   INTERFRAME_TIME_MS)
          
    # Set Enable to false  - to use full sensor size
    # Region s Region:<enable>,<min x>,<min y>,<size x>,<size y>   
    dvs.set("Region", "0,0,0,0,0") 

    # select the number of files you want in range() for some short integration times, 0-based
    # and the increment for what you want on the integration times in ms 
    for i in range(4):
        Exp_ms = i * 1 + 0.25
        dvs.set("Exposure", Exp_ms)
        #dvs.set("q2c_SetFileName", "./Integ_" + gain + "_{:.0f}".format(100*Exp_ms) + ".raw")
        # NOTE issue with colons in file name
        # Require escapeing with backslash
        # dvs.set("q2c_SetFileName", "C\:/temp/spectro.raw")
    
        # Update the UI controls
        # Important. Call this before, not After actionCapture!
        #
        dvs.refreshView()
        
        # Start capture 1 = Foreground , 0 = Background
        dvs.set("actionCapture", 1)

        

        # FrameWaiting works for acquires, but
        # saves to disk run in another thread, so 
        # we must poll the save state to continue safely. 
        # dvs.busy_poll("FrameWaiting") 
        #
        
        # We use this instead        
        res = dvs.waitForAcquireAndSave()
       
       
            
    
    
    #Example of setting a sub-region    
    ## Region s Region:<enable>,<min x>,<min y>,<size x>,<size y>   
    dvs.set("Region", "1,0,0,500,300")
    dvs.set("q2c_SetFileName", "./ForeSubRegion.raw")
    dvs.refreshView()
    dvs.set("actionCapture", 1)
    

    # Known bug - can't set the Sub Region checkbox from a script.
    # Setting to 500, will actually set to 496
    
    #
    # FrameWaiting works - but should not be used if another save follows
    # immmediately afterwards.  There is a bug that will clip the saved file
    # output if another acquisition is started before the save competed
    # on prior save. See waitForAcquireAndSave() above.
    #
    dvs.busy_poll("FrameWaiting") 

    dvs.epics_socket.close()    
    
    
    
    
# #
# #
# #
if __name__ == "__main__":
 
   main(sys.argv[1:])
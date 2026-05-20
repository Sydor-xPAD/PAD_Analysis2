# created 08122022 BWM
# program to collect linearity data for sCMOS

import DG645
import sys
import os
import socket
import time
import DV_socket

epics_cmd_port = 10030
DV_Address = "127.0.0.1"   # use 127.0.0.1 for local host


# start the program         
def main(argv):
    
   dvs = DV_socket.DataViewerSocket(DV_Address)
   dvs.set('NImages', 10) 
   
# software trigger (0), external trigger (3) 
   dvs.set("Trigger", 0)
   
# what gain are you using? "high" or "low" ? 
   gain = "high" 
   
# select the number of files you want in range() for some short integration times, 0-based
# and the increment you want on the integration times in ms 
   for i in range(4):
    Exp_ms = i * 500
    dvs.set("Esposure", Exp_ms)
    dvs.set("q2c_SetFileName", "./Integ_" + gain + str(Exp_ms) + ".raw",)
    dvs.set("actionCapture", 1)
    aquireTime = (Exp_ms * 10)/1000 + 2
    time.sleep(aquireTime)
    #dvs.busy_poll("FrameWaiting") # will work eventually 
    
# select the number of files you want in range() for some longer integration times, 0-based
# and the increment you want on the integration times in ms 
   for i in range(5):
    Exp_ms = (i + 1) * 2000
    dvs.set("Esposure", Exp_ms)
    dvs.set("q2c_SetFileName", "./Integ_" + str(Exp_ms) + ".raw",)
    dvs.set("actionCapture", 1)
    aquireTime = (Exp_ms * 10)/1000 + 2   # 10 images * exp_time, convert to seconds for "time" function, plus safety margin of 2
    time.sleep(aquireTime)
    #dvs.busy_poll("FrameWaiting") # will work eventually 
   
   # this has to be the last thing or the socket will close mid-experiment which would be sad
   dvs.epics_socket.close()    
# #
# #
# #
if __name__ == "__main__":

 

   main(sys.argv[1:])
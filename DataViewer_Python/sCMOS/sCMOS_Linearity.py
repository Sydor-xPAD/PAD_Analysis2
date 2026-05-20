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

# How to define com Port on Linux
#thecomport="/dev/ttyUSB0"
# In not Linux... 
thecomport="COM8"

# BURM=burst mode toggle, "TLVL=trigger level, "TSRC = trigger source 5= single shot", "BURC= burst count, "BURP= burst period"]
SRSInit = ["BURM 1", "TLVL 3.3", "TSRC 5", "BURC 10", "BURP 1e-3", "BURD 100e-3", 
           "DLAY 5,0,5e-7", "DLAY 7,0,5e-7"]
        # set D relative to C, set F relative to C; see SRS manual for number schemes

# start the program         
def main(argv):
   
   aSRS = DG645.srs(thecomport)
   aSRS.sendCommands(SRSInit, False)
   
   # start SRS in single trigger mode to turn off diode outputs for background
   print("Init Valuse SRS", SRSInit)
   dvs = DV_socket.DataViewerSocket(DV_Address)
   dvs.set('Exposure', 200)
   dvs.set('NImages', 1)
   dvs.set("InputTriggerEdge", 1)
   
# now triggering with free running rigol at .8 Hz to trigger both the SRS and camera
   #dvs.set("Trigger", 0)
   dvs.set("Trigger", 3)
   dvs.set("OutputTrigger", 0)
   dvs.set("q2c_SetFileName", "./back2.raw")   # get background image, rename manually to whatever 
   dvs.set("actionCapture", 1)
   #dvs.busy_poll("FrameWaiting")   # will work eventually and can get rid of sleep below 
   time.sleep(4)
   #set trigger to 
   aSRS.sendCommand("TSRC 1", False)

# set SRS back to external trigger from single mode
# select the number of files you want in range() 
# and the increment you want on the counts line as the last value for num of bursts per image
   for i in range(20):
    counts = (i + 1) * 2
    aSRS.sendCommand("BURC " + str(counts), False)
    dvs.set("q2c_SetFileName", "./Burst_" + str(counts) + ".raw",)
    dvs.set("actionCapture", 1)
    time.sleep(3)
    #SRS is being external triggerd by Rigol
    #aSRS.sendCommand("*Trg", False)
    #dvs.busy_poll("FrameWaiting")


# return conotrol back to local SRS 
# set trigger on SRS back to single to stop LEDs from fireing
   aSRS.sendCommand("TSRC 5", False)
   aSRS.sendCommand("LCAL", False)
   dvs.set("Trigger", 0)
   dvs.epics_socket.close()
# #
# #
# #
if __name__ == "__main__":

 

   main(sys.argv[1:])
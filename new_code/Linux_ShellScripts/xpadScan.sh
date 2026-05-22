#!/bin/bash
# File: xpadScan.sh
# 6/13/23 - YF - Inception
#Long Description:
#  TODO - more detail
#   NOTE - this script deletes the runs from previous times so it can overwrite
#   to the same run name.
#  LOOP:
#     Create a run. 
#     Run a python script to view a lineout over some area.
# Usage
#   xpadScan.sh <TODO>

set -x # show commands as they run
#
# USER SET CONSTANTS
#
##deltaT=10 # in ns
nFrames=2
integration=100; # in usec
interframe=100; # in usec
setname=${1:-xpadscan}  # Parameter 1 is setname  or if not specifiedf use -defaultname
RAIDPATH="/mnt/raid/keckpad"


#
# Define functions
#

take_background() {
    #
    #  Background image
    #
    ## assumes a hardware trigger
    $mmcmd "startrun vref_Back"  
    $mmcmd "status -wait"
    # Retrieve run 
    #$mmcmd "getframe -$nFrames"
}


# Path to binary
#mmcmd="/home/sydor/projects/mm-pad-client-cmdline/bin/debug/mmcmd"
mmcmd="mmcmd"

# run mmclient in script mode if not already running
../../PAD_SH/LaunchIfNeeded.sh


# TODO:warn if deleting first
# remove directories:
rm -r "$RAIDPATH"/set-$setname/run-run_*


$mmcmd open 1
$mmcmd stop

sleep 1


$mmcmd "Image_Count $nFrames"       #Set number of frames
$ger mmcmd "Interframe_Usec $interframe"  
$mmcmd "Integration_Usec $integration"
$mmcmd "SW_Trigger 1"



#set set name - $1 is passed in parameter
$mmcmd "startset $setname"


#Turn on power
#$mmcmd "Power_Control 1"

#sleep 2
#take_backgound  # call the function


  
#   $mmcmd "Shutter_Open 1"
#   sleep 1
 
	#  Foreground image
	#


	# #assumes a hardware trigger

   for i in {1..3}
   do
      #let "bias = 900 + i * 100"
      #$mmcmd "DFPGA_DAC_OUT_VREF_BUF $bias" 
      #$mmcmd "DFPGA_DAC_OUT_VREF_BP $bias"  

      runname="run_$i"
      echo "DEBUG: About to StartRun:$setname  $runname" 
      $mmcmd "startrun $runname"  
             
      $mmcmd "status -wait"
      # run the python analysis HERE
      ../plotlineout.py "$setname $runname 1 0 0 128 16"  # SetName RunName FrameNum zASICX zASICY ROIW ROIH 
      ## read  # Press return for debugging

   done
        
   #$mmcmd "status -wait -verbose"
   #$mmcmd "Shutter_Open 0"
   echo "Done."



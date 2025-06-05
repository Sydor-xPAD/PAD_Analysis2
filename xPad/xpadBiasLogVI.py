# Filename: xpadBiasLogVI.py
# This script queries the HV_CURRENT and HV_VOLTAGE 
# V 1.0 10/24/24
#---------------------------------------------------------

import time
import os
import sys
import io
import csv
import datetime

import subprocess

# start up mmclient listening on a pipe:
#mmclient -s -t &
#mmcmd open 1
#

#
#
#
def query_cmd( cmd_string ):
    """ Use subprocess to send commands to the mcmd shell command
    """

    res = 0
    # Run the shell command
    result = subprocess.run("mmcmd " + cmd_string, shell=True, capture_output=True, text=True)

    if len(result.stderr) >0:
        print("E! " + result.stderr)
        res = -1
    if len(result.stdout)>0:
        # Print the command output #DEBUG
        print(f"cmd:{cmd_string}, res:{result.stdout}")   
        resp = result.stdout
        if "=" in resp:
            tok  = resp.split("=")[1]
            return res, tok
            
    return res,result.stdout




#----------------------------------------------------------
# Set 'num_runs' and 'delay_between_capture_events' to the time you want to capture data
#
# Number of data points aka the number of times the script will run
num_runs = 9999
# how many seconds between each data point reading
delay_between_capture_events = 1

#-----------------------------------------------------------

#what time is it? to save the timestamp for the csv filename
timestamp_for_filename = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#main loop 
def go(num_runs):
    res = True
    list_commands = [
        "HV_Current[0]",
        "HV_Voltage[0]",
        "HV_Current[1]",
        "HV_Voltage[1]"

        ]
    




    #reset the standard output to the terminal
    sys.stdout = sys.__stdout__
        
    #get current working directory to save the csv file to parent folder
    cwd = os.getcwd()

    #define csv file name with timestamp for the beginning of the run
    filename = f"xpadLog.csv"

    #define the filepath the csv will be saved to
    filepath = os.path.join(cwd, filename)

    #create a loop to issue the mmclient commands
    for i in range(num_runs):

        buffer = ""
        #create timestamp for the individual temperature data points
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        buffer = timestamp 

        for c in list_commands:
            res, lines = query_cmd( c )   # run the command-line arguments
            buffer += "," + lines.strip()
            if res:  
                break

        

        # Add a delay in seconds between each run
        time.sleep(delay_between_capture_events)

        #parse the buffer content
        buffer_lines = buffer.strip()


        with open(filepath, "a", newline='') as f:      
            
            f.write(buffer_lines + "\n")
        



# Entry point of the script
if __name__ == "__main__":
    # Code to be executed when the script is run directly
    
    print("Start.")
    print(" ")  #blank line between readout and logging temperatures message 

    go(num_runs)    

    print("Fin.")  #blank line between readout and completion message


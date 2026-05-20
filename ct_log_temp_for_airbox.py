#the intent of this code is to log temp data for the AirBox13 through mmclient
#written by Christian Terjesen 2/26/24

import xpad_utils as xd
import time
import os
import sys
import io
import csv
import datetime


# Number of data points aka the number of times the script will run
num_runs = 10  
# how many seconds between each data point reading
num_secends = 1


#what time is it to save the timestamp for the csv filename
timestamp_for_filename = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#main loop 
def go(num_runs):
    telemetry_output = True
    list_commands = [
        "ADC_Sensor_Temperature",         # ask for temp values
        "ADC_Sensor_Low_Temperature"
        ]
    
    #create a buffer to store the terminal output
    buffer = io.StringIO()
    sys.stdout = buffer

    for i in range(num_runs):
        for c in list_commands:
            telemetry_output = xd.run_cmd( c )   # run the command-line arguments
            if telemetry_output:  
                break

        # Add a delay in seconds between each run
        time.sleep(num_secends)

        #parse the buffer content
        buffer_lines = buffer.getvalue().strip().split('\n')
        temperatures = []
        for line in buffer_lines:
            if 'temperature' in line.lower():
                temp_value = str(line.split('=')[-1].strip())
                temperatures.append(temp_value)

        #reset the standard output to the terminal
        sys.stdout = sys.__stdout__
        
        #get current working directory
        cwd = os.getcwd()

        #timestamp for the individual temperature data points
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #define csv file name with timestamp
        filename = f"temperature_data_{timestamp_for_filename}.csv"

        filepath = os.path.join(cwd, filename)

        #write the terminal output to the csv

        if not os.path.exists(filepath):
            header = ['Timestamp'] 
            for j in range(0, len(temperatures), 8):
                header.append('ADC_Sensor_Temperature_' + str(j +1))
            for j in range(8, len(temperatures), 16):
                header.append('ADC_Sensor_Low_Temperature_' + str(j +1))
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)

        with open(filepath, "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp] + temperatures)



# Entry point of the script
if __name__ == "__main__":
    # Code to be executed when the script is run directly
    print("Logging Temperatures...")

    go(num_runs)
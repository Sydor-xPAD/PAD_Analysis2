#!/usr/bin/env python3
# xpad_utils
# v1.0 6/28/23 YF - Created
#

import subprocess
import numpy as np


# Special conversion - Sensor ADC Temperature
#double StParameter::convertSensorTemperature(uint32_t raw) const
#{
#    double val = convertSensorVoltage(raw);
#    return (3.2057 * val * val) - (53.749 * val) + 77.421;  // Per MM Keck PAD FPGA Information v0.2
#}


def convertSensorTemp(raw):
    dval = convertSensorVoltage(raw)
    return (3.2057 * dval * dval) - (53.749 * dval) + 77.421  #   // Per MM Keck PAD FPGA Information v0.2

#//---------------------------------------------
#// Special conversion - Sensor Raw ADC Voltage
#double StParameter::convertSensorVoltage(uint32_t raw) const
#{
#    double val = (raw >> 4) & 0xfff;   // limit to 12 bits
#    if (val >= 2048)
#    {
#        val = val - 4096;
#    }
#    return ( (val / 4096.0) + 0.5) * 3.01; // Per Sect 4.3.7.1, spec v1.4
#}

def convertSensorVoltage(raw):
    val = (raw >> 4) & 0xFFF
    if val >= 2048:
        val = val - 4096

    return ( (val / 4096.0) + 0.5) * 3.01 # ; // Per Sect 4.3.7.1, spec v1.4


#// Special conversion - Sensor ADC Current
#double StParameter::convertSensorCurrent(uint32_t raw) const
#{
#    double val = convertSensorVoltage(raw);
#    return val / 2.09;         // Per MM Keck PAD FPGA Information v0.2
#}

def convertSensorCurrent(raw):
    dval = convertSensorVoltage(raw)
    return dval / 2.09


#
#
#
def run_cmd( cmd_string ):
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
    return res # 0 = success, -1 = error


def gradient_over_lineout( data_array):
    """ data_array should be a 1-D float[]
    """
    # Lets assume it is  a 128 lineout averaged over 16 - from a Tap
    # One option is to do a lineout - and return slope.
    X = range( len(data_array) )
    slope, intercept = np.polyfit(X, data_array, deg=1)
    R = np.corrcoef(X, data_array) # check.
    return slope,intercept

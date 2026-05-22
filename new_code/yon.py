#!/usr/bin/env python3
# YON.py
# Sort of the same as YON.mcmd - 
# run First to turn everything on.
# V 1.0 YF 6/30/23 - Created

import xpad_utils as xd


def go():
    res = True
    list_commands = [
        "power_con 1",         # sensor power on
        "HV_enable 1",          # sensor bias on 
        "HV_Output_Enable 1",
        # YF 2/7/23 Set the DACS
        "DFPGA_DAC_OUT_VGUARD 822",
        "DFPGA_DAC_OUT_VINJ 1644",
        "DFPGA_DAC_OUT_VREF_BUF 1233",
        "DFPGA_DAC_OUT_VREF_BP 1233",
        "DFPGA_DAC_OUT_VREF 1849",
        "DFPGA_DAC_OUT_V_ISS_BUF_PIX 719",
        "DFPGA_DAC_OUT_V_ISS_AB 668",
        "DFPGA_DAC_OUT_V_ISS_BUF 1297",
        #f"SW_Trigger 1",
        "ExposureMode 1", 
        "Readout_Mode 1",
        # Optional - Set the trigger to external
        "Trigger_Mode 2"
        ]
 
    
    for c in list_commands:
        res = xd.run_cmd( c  )   #Set number of frames
        if res:
            break


# Entry point of the script
if __name__ == "__main__":
    # Code to be executed when the script is run directly
    print("Start.")
    
    # Access the command-line arguments
    go()


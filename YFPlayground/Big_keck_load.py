#!/usr/bin/env python3
#created by BWM to take Kecks big data load
#8/30/22 first creation

# YF 6/23/23 - Tweaks
# v 1.0 6/29/23 - Converted to class object. See main in this file for example
# v 1.1 1/26/24 - Combine Keck and MMPAD data formats into one.
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import struct
import xpad_utils as xutil


# GLOBAL FLAGS
PRINT_METADATA = 0
#

 
class Metadata:
    __slots__ = ["frameParms", "lengthParms", "frameMeta", "capNum", "frameNum",
                 "integTime", "interTime", 
                 "v_iss_buf_pix", "v_iss_ab", "v_mon_out", "v_iss_buf",
                 "vdda_current", "vdda_volts", "sensorTemp" ]
    def __init__(self, fp,  lp,  fm, cn, fn, integ, inter, 
                 v_iss_buf_pix, v_iss_ab, v_mon_out,  v_iss_buf, vddaCurrent, vddaVolts, st):
        self.frameParms = fp
        self.lengthParms = lp
        self.frameMeta = fm
        self.capNum = cn
        self.frameNum = fn
        self.integTime = integ
        self.interTime = inter
        self.v_iss_buf_pix = v_iss_buf_pix
        self.v_iss_ab  = v_iss_ab
        self.v_mon_out = v_mon_out
        self.v_iss_buf = v_iss_buf
        self.vdda_current = vddaCurrent
        self.vdda_volts = vddaVolts
        self.sensorTemp = st


class KeckFrame:
    def __init__(self, filepath, imgType = 'KECK') -> None:
        """ type = "MMPAD" will load MMPAD images 
        """
        self.filepath = filepath
        self.dataFile = None
        self.numImages = 0
        self.imgType = imgType
        self.dtype = np.dtype('int16')
        self.footerSize = 1024 - 256
        self.readExtraByte = False

        self.oneImageSize = (1024+512*512*2) # KECK
        if imgType == 'MMPAD':
            self.oneImageSize = (2048+512*512*4) # MM
            self.dtype = np.dtype('int32')
            self.footerSize = 2048 - 256
            self.readExtraByte = True


        self.open()
        



    def open(self) -> bool:
        self.dataFile = open( self.filepath,"rb")
        if self.dataFile:
            self.numImages = int(os.path.getsize( self.filepath)/self.oneImageSize)
            return True

        return False
    

    def close(self):
        if (self.dataFile):
            self.dataFile.close()


    def getFrame(self):
        headerbytes = self.dataFile.read(16)  
        frameParms = struct.unpack("<HHHHII",headerbytes)
        headerbytes = self.dataFile.read(16) 
        lengthParms = struct.unpack("<IHHBB6x",headerbytes)
        headerbytes = self.dataFile.read(16)   # The first 48 are <?> in the file header
        if self.readExtraByte:
            headerbytes = self.dataFile.read(41)   # At 0x800000   to 0x800029
            frameMeta = struct.unpack("<QIIQIIIIB",headerbytes) # Q = 8, I = 4
        else:
            headerbytes = self.dataFile.read(40)   # At 0x800000   to 0x800029    
            frameMeta = struct.unpack("<QIIQIIII",headerbytes) # Q = 8, I = 4
        
        # ADDR   Param                              Index
        #  0x800000  Host Ref Tag           Q_1      0
        #  0x800004  Host Ref Tag           Q_2      0  
        #  0x800008  Global Frame Count     I       1
        #  0x80000C  GSeq Frame Count        I       2
        #  0x800010  Time Since Armed        Q_1     3
        #  0x800014  Time Since Armed        Q_2     3
        #  0x800018  IntegrationTime         I       4
        #  0x80001C  InterframeTime          I       5
        #  0x800020  various_metame          I       6
        #  0x800024  ReadoutDelay            I       7
        
        if self.readExtraByte:
            headerbytes = self.dataFile.read(256-(16+16+16+41)) #read remainder of header bytes
        else:
            headerbytes = self.dataFile.read(256-(16+16+16+40)) #read remainder of header bytes    

        # Actually these are all 0?
        s = 0
        SensorTemp = np.zeros( (8,1), dtype='int16')  # nope :-(
        for i in range(8):
            subModMetaData = headerbytes[s:s+24]
            subModMetaDataB = struct.unpack("<HHHHHHHHHHHH",subModMetaData) # 
            SensorTemp[i] = subModMetaDataB[9]
            s += 8

        
        frameNum = frameMeta[1]
        capNum = int(frameMeta[6]>>24) & 0xf
        integTime = frameMeta[4]
        interTime = frameMeta[5]
        #print(capNum)

        
        dt = self.dtype 
        data = np.fromfile(self.dataFile, count = (lengthParms[1] * lengthParms[2]), dtype = dt)
        footer = self.dataFile.read(self.footerSize) #read footer bytes 
        if self.imgType =='MMPAD':
            footerB = struct.unpack("<448I",footer) #  read into list of uint32
        else:            
            footerB = struct.unpack("<384H",footer) #  read into list of uint16
        

        # DEBUG
        #print (tuple(hex(num) for num in footerB) )
        # SubMod<N> Semsor Temp<N>
        #print( footerB[8],  footerB[8 + 1*12],  footerB[8 + 2*12], 
        #      footerB[8 + 3*12], footerB[8 + 4*12],  footerB[8 + 5*12], footerB[8 + 6*12], 
        #      footerB[8 + 7*12]  ) 

        v_iss_buf_pix = [footerB[i * 12] for i in range(8)]
        v_iss_ab = [footerB[1 + i * 12] for i in range(8)]
        v_mon_out = [footerB[2 + i * 12] for i in range(8)]
        v_iss_buf = [footerB[3 + i * 12] for i in range(8)]
        vdda_current = [footerB[4 + i * 12] for i in range(8)]
        vdda_voltage = [footerB[5 + i * 12] for i in range(8)]
        sensor_temp = [footerB[8 + i * 12] for i in range(8)]   # Sensor Temp

        # convert raw values to correct units
        cv_iss_buf_pix = [ xutil.convertSensorCurrent( x ) for x in v_iss_buf_pix  ]
        cv_iss_ab      = [ xutil.convertSensorCurrent( x ) for x in v_iss_ab  ]
        cv_mon_out     = [ xutil.convertSensorVoltage( x ) for x in v_mon_out  ]
        cv_iss_buf     = [ xutil.convertSensorVoltage( x ) for x in v_iss_buf  ]
        cvdda_current  = [ xutil.convertSensorCurrent( x ) for x in vdda_current  ]
        cvdda_volts    = [ xutil.convertSensorVoltage( x ) for x in vdda_voltage  ]
        csensor_temp   = [ xutil.convertSensorTemp( x )    for x in sensor_temp  ]

        if PRINT_METADATA:
            # Create a new list of formatted strings with 4 digits of precision
            temp = [ "{:10.4f}".format(x) for x in cv_iss_buf_pix ]; 
            print(f"iss_buf_pix {', '.join( temp )}" )
            temp = [ "{:10.4f}".format(x) for x in cv_iss_ab ];      
            print(f"iss_ab      {', '.join( temp )}" )
            temp = [ "{:10.4f}".format(x) for x in cv_mon_out ];     
            print(f"mon_out     {', '.join( temp )}" )
            temp = [ "{:10.4f}".format(x) for x in cv_iss_buf ];     
            print(f"iss_buf     {', '.join( temp )}" )
            temp = [ "{:10.4f}".format(x) for x in cvdda_current ];  
            print(f"vdda_curr   {', '.join( temp )}" )
            temp = [ "{:10.4f}".format(x) for x in cvdda_volts ];    
            print(f"vdda_V      {', '.join( temp )}" )
            temp = [ "{:10.4f}".format(x) for x in csensor_temp ];   
            print(f"Temper.     {', '.join( temp )}" )


        metadata= Metadata(frameParms, lengthParms, frameMeta, capNum, 
                    frameNum, integTime, interTime, 
                    cv_iss_buf_pix, cv_iss_ab, cv_mon_out, cv_iss_buf, cvdda_current, 
                    cvdda_volts, csensor_temp )


        # return a Tuple of metadata structure and the Array Data             
        return (metadata, data)





# Entry point of the script
if __name__ == "__main__":

    # Code to be executed when the script is run directly
    print("Start.")

    # Example, how to read an MM-PAD frame with the BKL library
    #MM_Fore = BKL.KeckFrame( foreFile , imgType = 'MMPAD')
    
    #fore_filepath = r"C:\Sydor Technologies\50KV_0C_1ms_cap0_f_00000001.raw" # "C:\Sydor Technologies\temptst_00000001.raw" # C:/mnt/raid/keckpad/set-yoram/run-2023-06-23-16-21-32/frames/2023-06-23-16-21-32_00000001.raw"
    #back_filepath = r"C:\Sydor Technologies\50KV_0C_1ms_cap0_b_00000001.raw" # "/mnt/raid/keckpad/set-yoram/run-2023-06-23-16-23-00/frames/2023-06-23-16-23-00_00000001.raw"

    #fore_filepath = r"C:\Sydor Technologies\50KV_0C_1ms_cap0_f_00000001.raw" # "C:\Sydor Technologies\temptst_00000001.raw" # C:/mnt/raid/keckpad/set-yoram/run-2023-06-23-16-21-32/frames/2023-06-23-16-21-32_00000001.raw"
    #back_filepath = r"C:\Sydor Technologies\50KV_0C_1ms_cap0_b_00000001.raw" # "/mnt/raid/keckpad/set-yoram/run-2023-06-23-16-23-00/frames/2023-06-23-16-23-00_00000001.raw"

    fore_filepath = r"C:\temp\lbs1-013_00000001.raw"
    back_filepath = r"C:\temp\lbs1-013_00000001.raw"
    
    Fore = KeckFrame(fore_filepath)
    Back = KeckFrame(back_filepath)

    for n in range( Fore.numImages):
        (mdF, dataF) = Fore.getFrame()
        (mdB, dataB) = Back.getFrame()

        print(mdF.frameNum, mdB.frameNum)

        data2dF = np.resize( dataF, [512,512])
        data2dB = np.resize( dataB, [512,512])

        fig,axs = plt.subplots(3,1)
        axs[0].imshow(data2dF)
        axs[1].imshow(data2dB)
        axs[2].imshow(data2dF-data2dB)
        plt.show()

    Fore.close()
    Back.close()
    

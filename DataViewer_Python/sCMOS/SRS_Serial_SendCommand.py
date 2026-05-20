#!/usr/bin/python

#File: SRS_Serial_SendCommand.python
# 7/30/21
# Usage python SRS_Serial_SendCommand "*IDN?"

import serial
import time
import sys

thecomport="COM5"


def ShowHelp():
   print( "Send a command over serial port to SRS DG645.")
   print ("Usage:")
   print (sys.argv[0] + " <cmd>")


def init(port):
    """
    port is com port, such as "COM3"
    """
    ser=serial.Serial()
    ser.port = port
    ser.baudrate = 19200
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout= 1
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.writeTimeout = 1
    return ser

# When we send a serial command, the program will check and print
# the response given by the drive.
def send(ser,command,bQuery):
    ser.write((command+'\r\n').encode())

    if bQuery:
       response = ser.read_until()
    
       if len(response) > 0:
           print (response.decode())
           ser.flushInput()

       return response
    return ""   

def setup(ser):
    """
    Setup SRS DG645 
    """
    send(ser,'*CLS') # Clear 
        

#
# port is "COM3"
def tryConnect( port ):    
    """
    Returns ser if connects OK
    """
    try:
        ser = init(port) # Initialise the serial port
        ser.open()         # open the serial port
        return ser
        
    except Exception as e:
        print ('error opening serial port')
        
    return None



def sendCommand(port, cmd, bQuery):
   ser = tryConnect(port);
   if ( ser and ser.isOpen() ):
     
      try:

         send(ser, cmd, bQuery) 
         # *IDN?: will return
         # b'Stanford Research Systems,DG645,s/n008011,ver1.19.118\r\n'

         ser.close()


      except Exception as e1:
         print ("Error Communicating...: " + str(e1))
    

   else:
      print ("Could not open serial portError.\r\n");
   
      
   
#
#
#
def main(argv):
   print("Hello from Main")
   
   if len(argv) < 1:
      ShowHelp()
      sys.exit()
      
   
   bQuery=0
   if argv[0].find("?") > 0 :
      bQuery = 1
      
   cmd = argv[0]   
   sendCommand( thecomport, cmd, bQuery )   


#
#
#
if __name__ == "__main__":
   main(sys.argv[1:])

    

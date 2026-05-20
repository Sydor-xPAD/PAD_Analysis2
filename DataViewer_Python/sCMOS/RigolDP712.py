#!/usr/bin/python

#File: KA3005P.py
# 5/6/22

# Command Syntax:
# https://sigrok.org/wiki/Korad_KAxxxxP_series#Protocol
# This works through a keyspan or directly with USB
# Use Device manager to get com port and set it below. 

import serial
import time
import sys

thecomport="COM8"
kQUERY="*IDN?\n"
cmds = []


def ShowHelp():
   print( "Set a voltage. Works with the Korad 3005P.")
   print ("Usage:")
   # Using enumerate()
   for i, val in enumerate(cmds):
      print("   ", val[1] )
      

# Methods for accessing from other modules
# 
def Korad_ReadVoltage(port):
   resp = send(port, "VOUT1?", 1) # VOUT is actual voltage, not setpoint.
   return resp


def Korad_SetVoltage(port,v):
   """ float v in c parlance
   """
   astring = "VSET1:{:.2f}".format(v)
   resp = send(port, astring, 1) # VOUT is actual voltage, not setpoint.
   return resp

def Korad_tryConnect( port = thecomport):    
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


def init(port):  
    """
    port is com port, such as "COM3"
    """


    ser=serial.Serial()
    ser.port = port
    ser.baudrate = 9600
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 1
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.writeTimeout = 1 # try  https://stackoverflow.com/questions/39032581/python-serial-write-timeout?msclkid=06a7b07dd0b811ecb88765e3483d86bd

    return ser


def checkStatus(port, *argv):
   """
   returns 1 if all checks ok
   """
   ret = -1
   resp = sendCommand(port, kQUERY, 1)
   if resp != None:
      if resp.upper().startswith("KORADKA3005"):
         ret = 1
      print(kQUERY + ":" +resp)

   resp = sendCommand(port, "VSET1?", 1)
   if (resp != None):
      print("VSET1?" + ":" +resp)

   resp = sendCommand(port, "VOUT1?", 1)
   if (resp != None):
      print("VOUT1?" + ":" +resp)



def readVoltage(port,  *argv):
   """
   """
   ret = -1

   resp = sendCommand(port, "VOUT1?", 1) # VOUT is actual voltage, not setpoint.
   print(resp)
   return resp
   

def setVoltage(port, *argv):
   """
   """
   sendCommands( port, [ "OUT1", "VSET1:" + argv[0][0] ], 0 )
   
  
def send(ser,command,bQuery):
    #ser.write((command+'\r\n').encode())  # \r\n\ NO work
    ser.write((command).encode()) #NO LINE TERMINATION - works!
   
    

    if bQuery:
       response = ser.read_until()
    
       if len(response) > 0:
           # debug print (response.decode())
           ser.flushInput()

       return response.decode() # convert bytes back to string (sheesh)
    return ""   

def setup(ser):
    """
    Setup TODO
    """
    #TODOsend(ser,'*CLS') # Clear 
        




def sendCommand(port, cmd, bQuery):
   """ returns response if bQuery is 1
   """
   response = ""
   ser = Korad_tryConnect(port);
   if ( ser and ser.isOpen() ):
     
      try:

         response = send(ser, cmd, bQuery) 
          # https://github.com/pyserial/pyserial/issues/226?msclkid=3cea1283d0b911eca085a1264b72fdc5
         ser.flushInput()
         ser.flushOutput()
         ser.close()


      except Exception as e1:
         print ("Error Communicating...: " + str(e1))
    

   else:
      print ("Could not open serial portError.\r\n");

   return response   


def sendCommands(port, listofcmds, bQuery):
   """ returns response if bQuery is 1
   """
   response = ""
   ser = Korad_tryConnect(port);
   if ( ser and ser.isOpen() ):
     
      try:

         for c in listofcmds:
            response = send(ser, c, bQuery)
            time.sleep(.5)
            
         ser.close()


      except Exception as e1:
         print ("Error Communicating...: " + str(e1))
    

   else:
      print ("Could not open serial portError.\r\n");

   return response   

   
#
#
#
def main(argv):
   

   cmds.append( ["CHECK", "check -- returns connection status check", checkStatus] )
   cmds.append( ["V", "V #  --  # is volts 0-30", setVoltage]  )
   cmds.append( ["V?", "V?  -- Read actual voltage", readVoltage]  )
   



   if len(argv) < 1:
      ShowHelp()
      sys.exit()
      
   
      
   bQuery=1

   # MAGIC Happens Here *** Match the command and run the function

   parsed = 0
   for i, val in enumerate(cmds):
      if argv[0].upper() == val[0]:
        val[2](thecomport, argv[1:])
        parsed=1
        break
      
      
  
   if parsed == 0:
      print("syntax error :-( ")
   ##sys.exit("fin")


   
#
#
#
if __name__ == "__main__":

   # unit testing  # Comment out for final
   #sys.argv = ["KoradKA3500P", "check"]  # debug remove
   #main(sys.argv[1:])
   
   #sys.argv = ["KoradKA3500P", "V","1.23"]  # debug remove
   #main(sys.argv[1:])
   
   #sys.argv = ["KoradKA3500P", "V?"]  # debug remove
   #main(sys.argv[1:])
   
   ## ## ## End Unit Testing

   main(sys.argv[1:])
   
   

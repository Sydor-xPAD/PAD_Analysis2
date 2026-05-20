
from urllib import response
import serial
import time
import sys
#how to define port on Windows
#thecomport="COM1"
#How to define com Port on Linux
thecomport="/dev/ttyUSB0"
kQUERY="*IDN?"
cmds = []


# def ShowHelp():
#    print( " Works with the SRS DG645.")
#    print ("Usage:")
#    # Using enumerate()
#    for i, val in enumerate(cmds):
#       print("   ", val[1] )
      

# Methods for accessing from other modules
# 

def tryConnect( port = thecomport):    
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
    ser.baudrate = 115200
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 1
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.writeTimeout = 1 # try  https://stackoverflow.com/questions/39032581/python-serial-write-timeout?msclkid=06a7b07dd0b811ecb88765e3483d86bd

    return ser


def send(ser,command,bQuery):
    ser.write((command+'\n').encode())  #DP712 requires \n line feed termination
    #ser.write((command).encode()) #NO LINE TERMINATION - works for Korad not Rigol
   
    

    if bQuery:
       response = ser.read_until()
    
       if len(response) > 0:
           # debug print (response.decode())
           ser.flushInput()

       return response.decode() # convert bytes back to string (sheesh)
    return ""   


        





class srs():
   # a class to send any command string to SRS box
   def __init__(self,port):
      self.port = port

   def sendCommand(self, cmd, bQuery=True):
      """ returns response string if bQuery is 1
      """
      response = ""
      ser = tryConnect(self.port);
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

   def sendCommands(self, listofcmds, bQuery=True):
      """ returns response if bQuery is 1
      """
      response = ""
      ser = tryConnect(self.port);
      if ( ser and ser.isOpen() ):
      
         try:

            for c in listofcmds:
               response = send(ser, c, bQuery)
               time.sleep(.5)

            ser.flushInput()
            ser.flushOutput()  
            ser.close()


         except Exception as e1:
            print ("Error Communicating...: " + str(e1))
      

      else:
         print ("Could not open serial portError.\r\n");

      return response   

   def sendCommandAndReadback(self, cmd, param):
      """ Send a generic command, then query back response
      """
      response = ""
      ser = tryConnect(self.port);
      if ( ser and ser.isOpen() ):
         
         try:

            send(ser, cmd + param, False) 
               # https://github.com/pyserial/pyserial/issues/226?msclkid=3cea1283d0b911eca085a1264b72fdc5
            
            response = send(ser, cmd + "?", True) 
            ser.flushInput()
            ser.flushOutput()
            ser.close()


         except Exception as e1:
            print ("Error Communicating...: " + str(e1))
         

      else:
         print ("Could not open serial portError.\r\n");

      return response   

SRSInit = ["BURM 1", "TLVL 3.3", "TSRC 5", "BURC 100", "BURP 1e-3"]
#
#
#
def main(argv):
   
   # try
   aSRS = srs(thecomport)
   aSRS.sendCommands(SRSInit, False)
   

   print("Init Valuse SRS", SRSInit)
   #r2 = aSRS.sendCommandAndReadback("BURM", "0")
   #print("r2 is", r2)

   bSRS = srs(thecomport)
   bSRS.sendCommand("*  Trg", False)
   bSRS.sendCommand("LCAL", False)
   #rb = bSRS.sendCommand("BURM?", True)


   # if len(argv) < 1:
   #    ShowHelp()
   #    sys.exit()
      
   
      
   bQuery=1

   # MAGIC Happens Here *** Match the command and run the function

#    parsed = 0
#    for i, val in enumerate(cmds):
#       if argv[0].upper() == val[0]:
#         val[2](thecomport, argv[1:])
#         parsed=1
#         break
      
      
  
#    if parsed == 0:
#       print("syntax error :-( ")
#    ##sys.exit("fin")


   
# #
# #
# #
if __name__ == "__main__":

   # unit testing  # Comment out for final
   #sys.argv = ["RigolKA3500P", "check"]  # debug remove
   #main(sys.argv[1:])
   
   #sys.argv = ["RigolKA3500P", "V","1.23"]  # debug remove
   #main(sys.argv[1:])
   
   #sys.argv = ["RigolKA3500P", "V?"]  # debug remove
   #main(sys.argv[1:])
   
   ## ## ## End Unit Testing

   main(sys.argv[1:])
   
   

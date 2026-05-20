#!/usr/bin/python
import os
import sys
import time
import socket
import serial
from datetime import datetime
import traceback



# File: 
# Description: dg645.py

# Version History
#  7/11/23 v 1.0 Inception


#
VERBOSE = 2  # set to 0 to be silent, set to 1 to get some debug output, 2 to get more

# Enter a value of 1 for TCP or 2 for Serial Port
CONNECTION_TYPE = 1  

# SET the device IP Address below # Only used if CONNECTION_TYPE == 1
TCP_SOCKET_PORT=5024 ## sheesh. This is what the DG645 uses.

#IP_ADDR="192.168.11.58"
IP_ADDR="192.168.11.225"
#
## or set serial port # Only used if CONNECTION_TYPE == 2
#
PORT="com3"


class comObject:
    """
    Supports either TCP or COM port I/O to xxx
    """

    
    # init method or constructor
    def __init__(self, comType, ip_addr, port = TCP_SOCKET_PORT):
        self.comms = None
        self.comType = comType
        self.ip_addr = ip_addr
        self.port = port
        self.verbose = VERBOSE
        self.interCommandDelay = 0.1

    def open_serial(self):
        """
        port is com port, such as "COM3"
        returns a SerialPort
        """
        ser=serial.Serial()
        ser.port = self.port
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


    def open_socket(self):
        """
        port is TCP port such as 23
        returns a socket
        """
        comm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        comm_socket.connect( (self.ip_addr, self.port))
        comm_socket.settimeout( 1.0 ) # seconds
        return comm_socket

    #
    #
    #
    def tryConnect( self ):    
        """
        type 1 = TCPIP, 2 = COMM Port, else undefined
        Returns socket or serial port if connects OK
        """

        if (self.comType == 1):
            try:
                if self.verbose:
                    print("Opening socket:" + str(self.ip_addr) + ":" + str(self.port) )
                self.comms = self.open_socket() 
                return self.comms
                
            except Exception as e:
                print ('error opening TCP Port')
                
            return None

        if (self.comType == 2):
            try:
                if self.verbose:
                    print("Opening Serial:" + str(self.port) )
                self.comms = self.open_serial() # Initialise the serial port
                self.comms.open()         # open the serial port
                return self.comms
                
            except Exception as e:
                print ('error opening serial port')
                
            return None

        return None


    def send(self, cmd):
        """
        send without query
        """
        recv = None
        if self.comms == None:
            return None     # Error. not open

        if self.verbose:
            print(cmd + " : ", end="")

        if self.comType == 1:   
            self.comms.send( cmd.encode() ) 
            time.sleep(self.interCommandDelay);

        if self.comType == 2:
            self.comms.write( cmd.encode())
            time.sleep(self.interCommandDelay);



    def query(self, cmd):
        """
        send a query - return a string response
        """
        recv = None
        if self.comms == None:
            return None     # Error. not open

        if self.verbose:
            print(cmd + " : ", end="")

        if self.comType == 1:   
            self.comms.send( cmd.encode() ) 
            time.sleep(self.interCommandDelay);
            recv = self.comms.recv(1000).decode()
            time.sleep(self.interCommandDelay);

        if self.comType == 2:
            self.comms.write( cmd.encode())
            time.sleep(self.interCommandDelay);

            response = self.comms.read_until()
            if len(response) > 0:
                recv = response.decode()

        if self.verbose:
            print(recv)        
        return recv        


    def parse(self, strResponse):
        pass            
        return None  


#
#
#

class DG645:
    """
    """
    
    # init method or constructor
    def __init__(self, comObject):
        self.verbose = VERBOSE
        self.comObject = comObject
        self.EOL = "\r"

    def send(self, cmd):
        self.comObject.send(cmd + self.EOL)


    def query(self, cmd):
        return self.comObject.query(cmd + self.EOL)


    def setDelay(self, nChannel_c, nChannel_d, fDelay):
        """Delay SRS manual page 56
           DLAY 2,0,10e-6<CR> Set channel A delay to equal channel T0 plus 10 µs.
        """
        s = f"DLAY {nChannel_c},{nChannel_d},{fDelay}"
        self.send(s);

    def doTrigger(self):
        s = f"*TRG"
        self.send(s);

    def setTriggerSource(self, i):
        s = f"TSRC {i}"
        self.send(s);


    def setBurstOptions( self, nCount, fTriggerDelay, fBurstPeriod,  T0_only):
        s = f"BURC {nCount}"
        self.send(s);
        time.sleep( 100 );

        s = f"BURD {fTriggerDelay}"
        self.send(s);
        time.sleep( 100 );

        s = f"BURP {fBurstPeriod}"
        self.send(s);
        time.sleep( 100 );

        s = f"BURT {T0_only}"
        self.send(s);
        time.sleep( 100 );

    
    def setBurstMode(self, bEnable):
        """ bEnable is a boolean:True or False
        """
        n = 1 if bEnable else 0
        s = f"BURM {n}"
        self.send(s);

        


#
#
#
def ShowHelp():
   
   print ("Usage:")
   print (sys.argv[0]) # No command line params


    
      
   
#
#
#
def main(argv):
    r = None
    if CONNECTION_TYPE == 1:
        c = comObject( 1, IP_ADDR, TCP_SOCKET_PORT )
        r = c.tryConnect()
   
    if CONNECTION_TYPE == 2:
        c = comObject( 1, None, PORT )
        r = c.tryConnect()

    if (r):
        #now = datetime.now() # current date and time
        #date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        dg = DG645(c)
        dg.setDelay(2,0,50e-6)
        
    else:
        if c.verbose:
            print("Error, Could not connect")


    if r:
        if c.verbose:
            print("Close connection")
        c.comms.close()


    print("DONE!")


   
  
  


#
#
#
if __name__ == "__main__":
   main(sys.argv[1:])

    
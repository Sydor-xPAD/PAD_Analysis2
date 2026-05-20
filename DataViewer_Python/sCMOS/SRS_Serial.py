#!/usr/bin/python

#File: SRS_Serial.python
# 7/30/21


import serial
import time


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
    ser.timeout= 1
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.writeTimeout = 1
    return ser

# When we send a serial command, the program will check and print
# the response given by the drive.
def send(ser,command):
    ser.write((command+'\r\n').encode())
    #response = ser.read(1000).decode()
    #print("W:" + str(ser.in_waiting))
    response = ser.read_until()
    
    if len(response) > 0:
        print (response)
        ser.flushInput()

    return response    

def setup(ser):
    """
    Setup SRS DG645 
    """
    send(ser,'*CLS') # Clear 
        


def tryConnect():    
    """
    Returns ser if connects OK
    """
    try:
        ser = init("COM5") # Initialise the serial port
        ser.open()         # open the serial port
        return ser
        
    except Exception as e:
        print ('error opening serial port')
        
    return None


if __name__ == "__main__":
   
    interactive = 1
    ser = tryConnect();
    
    if ( ser and ser.isOpen() ):
        try:

            if interactive == 1:
                print("Welcome to program.\n")

            ser.flushInput()
            ser.flushOutput()

            setup(ser) 
            send(ser, '*IDN?')  # Tests the communication
            # should get back:
            # b'Stanford Research Systems,DG645,s/n008011,ver1.19.118\r\n'

            ser.close()


        except Exception as e1:
            print ("Error Communicating...: " + str(e1))
    else:
        print ("Cannot open serial port ")


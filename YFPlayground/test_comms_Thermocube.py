import serial
import struct
from bitstruct import pack
from enum import IntEnum
import time

LINUX = 0
WINDOWS = 1

class ThermoCube:
   class ControlParameter(IntEnum):
      CHILLER_SET_POINT_TEMP = 0b00001 # Returns 2 Bytes
      CURRENT_FLUID_TEMP = 0b01001     # Returns 2 bytes
      CHILLER_FAULTS = 0b01000         # Returns 1 byte

   def __init__(self, port, baudrate=9600):
      self.ser = serial.Serial(port, baudrate, timeout=1)

   def encode_command_byte(self, remote_control, chiller_on, from_master, parameter):
      return pack('u1u1u1u5',
                  int(remote_control),
                  int(chiller_on),
                  int(from_master),
                  parameter)

   # def set_temperature(self, temp_celsius):
   #    temp_fahrenheit = (temp_celsius * 9/5) + 32
   #    temp_value = int(temp_fahrenheit * 10)  # Convert to 0.1°F increments

   #    # Remote control, chiller on, remote to chiller, set point temp
   #    command_byte = 0b10100001
   #    # Pack as big-endian unsigned short
   #    data_bytes = struct.pack('>H', temp_value)

   #    self.ser.write(bytes([command_byte]) + data_bytes)

   #    # Wait for response (you might need to adjust this based on the chiller's behavior)
   #    response = self.ser.read(3)
   #    if len(response) == 3:
   #       return True
   #    return False


   # Function to encode temperature data
   def encode_temperature(self, temp_celcius):
      temp_fahrenheit = (temp_celcius * 9/5) + 32
      temp_value = int(temp_fahrenheit * 10)  # Convert to 0.1°F increments
      return pack('>u16', temp_value)  # Bi

   def close(self):
      self.ser.close()


# Usage
if __name__ == "__main__":


   print("Start.")

   # test bitstruct
   if LINUX:
      chiller = ThermoCube("/dev/ttyUSB0")  # Replace with your actual port
   elif WINDOWS:
      chiller = ThermoCube("COM4:")  # Replace with your actual port
      
      
   if 1:   
      # Example usage
      command_byte = chiller.encode_command_byte(
         remote_control=True,
         chiller_on=True,
         from_master=True,
         parameter=chiller.ControlParameter.CHILLER_SET_POINT_TEMP
      )

      print("DEBUG:", command_byte.hex())

      data_bytes = chiller.encode_temperature(15)
      full_message = command_byte + bytes([data_bytes[1]]) + bytes([data_bytes[0]])
      
      print("Set temperature message:", full_message.hex())
      chiller.ser.write(bytes(full_message))

      
      time.sleep(5)
   # ===================================
   # Example: Read set point temperature

   command_byte = chiller.encode_command_byte(
       remote_control=True,
       chiller_on=True,
       from_master=False,
       parameter=chiller.ControlParameter.CHILLER_SET_POINT_TEMP
   )
   chiller.ser.write(bytes(command_byte))
   response = chiller.ser.read(2)
   uint16_value = struct.unpack('<H', response)[0]
   
   if len(response) == 2:
      print("DEBUG", uint16_value, hex(uint16_value))

   time.sleep(5)
   # ===================================
   # Example: Read faults

   command_byte = chiller.encode_command_byte(
       remote_control=True,
       chiller_on=True,
       from_master=False,
       parameter=chiller.ControlParameter.CHILLER_FAULTS
   )
   chiller.ser.write(bytes(command_byte))
   response = chiller.ser.read(1) # Faults returns 1 byte
   if len(response) == 1:
      print("DEBUG", response[0], hex(response[0]))


   time.sleep(5)
   # ===================================
   # Example: Read Fluid Temp

   command_byte = chiller.encode_command_byte(
       remote_control=True,
       chiller_on=True,
       from_master=False,
       parameter=chiller.ControlParameter.CURRENT_FLUID_TEMP
   )
   chiller.ser.write(bytes(command_byte))
   response = chiller.ser.read(2) # Faults returns 1 byte
   if len(response) == 2:
      uint16_value = struct.unpack('<H', response)[0]

      print("DEBUG", uint16_value, hex(uint16_value))


   chiller.close()

   print("Fin.")
   


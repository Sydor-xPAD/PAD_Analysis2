import serial
import struct
from bitstruct import pack
from enum import IntEnum
import time

LINUX = 0
WINDOWS = 1

# testing
#globals
HEAD_IS_ON = True
HUMIDITY = 10

def convert_to_C(tempF):
   return (tempF-32)*5/9


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

   

   # Function to encode temperature data
   def encode_temperature(self, temp_celcius):
      temp_fahrenheit = (temp_celcius * 9/5) + 32
      temp_value = int(temp_fahrenheit * 10)  # Convert to 0.1°F increments
      return pack('>u16', temp_value)  # Bi

   def close(self):
      self.ser.close()


def Start_Monitor_Loop( chiller ):
   """ Read water Temp and Faults every N seconds
   """
   global HEAD_IS_ON, HUMIDITY
   # Example: Read set point temperature

   water_temp = -1
   water_setpoint = -1
   set_chiller_temp = -99
   indicator = "yellow"
   
   
   while True:
      
      indicator_int = ""
      
      command_byte = chiller.encode_command_byte(
         remote_control=True,
         chiller_on=True,
         from_master=False,
         parameter=chiller.ControlParameter.CHILLER_SET_POINT_TEMP
      )
      
      chiller.ser.write(bytes(command_byte))
      response = chiller.ser.read(2)
      
      if len(response) == 2:
         uint16_value = struct.unpack('<H', response)[0]
         water_setpoint = convert_to_C(uint16_value/10.0)
         print(f"SetPoint: {uint16_value}, {hex(uint16_value)}, Deg in C:{water_setpoint:.2f}")

      else:
         print("[MODAL]: Can not communicate with Chiller.  Please verify Chiller is ON and connected.")
         indicator_int = "red"
         
         
      
      command_byte = chiller.encode_command_byte(
         remote_control=True,
         chiller_on=True,
         from_master=False,
         parameter=chiller.ControlParameter.CURRENT_FLUID_TEMP
      )
      
      chiller.ser.write(bytes(command_byte))
      response = chiller.ser.read(2)
      
      if len(response) == 2:
         uint16_value = struct.unpack('<H', response)[0]
         water_temp = convert_to_C(uint16_value/10.0)
         print(f"Fluid Temp: {uint16_value}, {hex(uint16_value)}, Deg in C:{water_temp:.2f}")

      else:
         print("[MODAL]: Can not communicate with Chiller.  Please verify Chiller is ON and connected.")
         indicator_int = "red"
         
         
      time.sleep(5)
      
      if indicator_int == "":
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
            print("Faults:", response[0], hex(response[0]))
            if response[0] != 0:
               print(f"[MODAL]: Caution. There is a chiller fault, code {response[0]}")
               
         else:
            print("[MODAL]: Can not communicate with Chiller.  Please verify Chiller is ON and connected.")   
            indicator_int = "red"

      

         if HEAD_IS_ON:
            if HUMIDITY == 0 :
               indicator_int = "red"   # treat 0 as cant com with Humidity sensor
            elif HUMIDITY < 20:
               if abs(water_setpoint-5) > 0.5:
                  set_chiller_temp = 5
               indicator_int = "green"
                  
            else:
               if abs(water_setpoint-15) > 0.5:
                  set_chiller_temp = 15
               indicator_int = "yellow"
         else:
            set_chiller_temp = 15        
            indicator_int = "yellow" 
            
               

         if set_chiller_temp > -99:
            command_byte = chiller.encode_command_byte(
               remote_control=True,
               chiller_on=True,
               from_master=True,
               parameter=chiller.ControlParameter.CHILLER_SET_POINT_TEMP
            )
            

            # print("DEBUG:", command_byte.hex())

            data_bytes = chiller.encode_temperature( set_chiller_temp)
            full_message = command_byte + bytes([data_bytes[1]]) + bytes([data_bytes[0]])
            
            print("Set temperature message:", full_message.hex())
            chiller.ser.write(bytes(full_message))
            set_chiller_temp = -99   
            
      if indicator_int != "":
         indicator = indicator_int         

      print ("Indicator is", indicator)   
      time.sleep(5)

      
#      
#  M A I N      
#
if __name__ == "__main__":
   
   print("Start.")

   # test bitstruct
   if LINUX:
      chiller = ThermoCube("/dev/ttyUSB0")  # Replace with your actual port
   elif WINDOWS:
      chiller = ThermoCube("COM4")  # Replace with your actual port
      
   
   if 1:
      Start_Monitor_Loop( chiller )   
      
   
   #
   #  ^ Does not return
   #   
   
   
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
      print("DEBUG", uint16_value, hex(uint16_value), "Deg in C:", convert_to_C(uint16_value/10.0))

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
      print("Faults:", response[0], hex(response[0]))


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
   


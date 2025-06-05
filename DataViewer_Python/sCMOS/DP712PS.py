#created 8/2/22 BWM
###########################
#Program to talk to Rigol DP712 power supply

import easy_scpi as scpi
import os
import numpy as np
from dp700 import PowerSupply
comPort = "COM8"
port = None, 
timeout = 5,
read_termination = '\n', 
write_termination = '\n' 


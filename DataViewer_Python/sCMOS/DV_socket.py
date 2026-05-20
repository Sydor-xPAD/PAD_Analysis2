import sys
import time
import socket
import select

class DataViewerSocket:
    def __init__(self, dest_addr, dest_port = 10030):
        self.epics_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.epics_socket.connect((dest_addr, dest_port))
        self.cmd_dict = { \
            'Exposure': 'd', 
            'NImages': 'i32', 
            'CaptureMode': 'i32', 
            'NFrames': 'i32', 
            'Resolution': 'i32', 
            'Region' :'s',
            'Mode': 'i32', 
            'Interframe': 'd', 
            'Trigger': 'i32', 
            'FrameWaiting': 'i32', 
            'q2c_SetFileName' : 's', 
            'actionCapture' : 'i32', 
            'actionAbort': 'i32', 
            'InputTriggerEdge' : 'i32', 
            'OutputEdge': 'i32', 
            'OutputTrigger' : 'i32', 
            'Gain' : 'd', 
            'Trigger' : 'i32',
            'FrameWaiting' :'i32',
            
        }
        # InputTriggerEdge: 1 = Rising, 0 = Falling
        # OutputEdge: 1 = Rising, 0 Falling
        # OutputTrigger: 0 = Low
        #                1 = High
        #                2 = NA
        #                3 = Exposure Start
        #                4 = Global Exposure
        #                5 = Readout End
        # Trigger: 0 = Software
        #          1 = Std
        #          2 = Sync
        #          3 = Global
        self.cmd_interval = 1
        self.cmd_count = 0

    """
    Send a command in a loop, until response is 0.
    """
    def busy_poll(self, cmd_str, max_tries = -1):
        try:
            cmd_type = self.cmd_dict[cmd_str]
        except KeyError:
            print('Command {} not found.'.format(cmd_str))
            return -2
        socket_str = self.wrap_get2(cmd_str, cmd_type)
        while True:             # -=-= TODO Add in max tries
            epics_response = self.send_cmd(socket_str)
            if (type(epics_response) == int): # An error occurred
                return -1
            try:
                check_val = int(epics_response.split(':')[3])
            except:    
                check_val = 0
                
            if (check_val == 0):
                break

            time.sleep(.5)      # Wait to try again
        return 0
            
    def set(self, cmd_str, cmd_val):
        try:
            cmd_type = self.cmd_dict[cmd_str]
        except KeyError:
            print('Command {} not found.'.format(cmd_str))
            return -2
        
        socket_str = self.wrap_set2(cmd_str, cmd_val, cmd_type)
        #-=-= TODO We could probably put the delay in a better place
        socket_resp = self.send_cmd(socket_str)
        time.sleep(self.cmd_interval) # Put in the pause here
        return socket_resp
    
    def get(self, cmd_str):
        try:
            cmd_type = self.cmd_dict[cmd_str]
        except KeyError:
            print('Command {} not found.'.format(cmd_str))
            return -2

        socket_str = self.wrap_get2(cmd_str, cmd_type)
        #-=-= TODO We could probably put the delay in a better place
        socket_resp = self.send_cmd(socket_str)
        time.sleep(self.cmd_interval) # Put in the pause here
        return socket_resp
    
    def send_cmd(self, socket_str, timeout = 2):
        print("Sending command: {}".format(socket_str))
        bytes_sent = self.epics_socket.send(socket_str.encode())
        read_list, write_list, err_list = select.select([self.epics_socket], [], [], timeout)
        if (len(read_list) == 0):
            print("No read data.")
            return -1
        epics_response = self.epics_socket.recv(4096)
        print("Response: {}".format(epics_response.decode()))
        return epics_response.decode()
    
    def wrap_set2(self, command, val, data_type = None):
        #The default None value lets us see if the parameter was specified in the call.
        if data_type is None:
            data_type = self.default_type

        out_str = "#{}:setpv<{}>:{}:{}\r\n".format(self.cmd_count, data_type, command, val)
        self.cmd_count = self.cmd_count + 1
        return out_str

    def wrap_get2(self, command, data_type = None):
        out_str = "#{}:getpv<{}>:{}?\r\n".format(self.cmd_count, data_type, command)
        self.cmd_count += 1
        return out_str
    
    #
    # Special command to update UI
    #
    def refreshView(self):
        cmd = "!LRefreshView"
        socket_str = cmd + "\r\n"
        print("Sending command: {}".format(socket_str))
        bytes_sent = self.epics_socket.send(socket_str.encode())   
     
         
    #
    # Special command to Query File Save Status
    #
    def queryAcqStatus(self):
        cmd = "!LQueryAcqStatus?"
        socket_str = cmd + "\r\n"
        print("Sending command: {}".format(socket_str))
        bytes_sent = self.epics_socket.send(socket_str.encode())   
        epics_response = self.epics_socket.recv(4096)
        print("Response: {}".format(epics_response.decode()))
        # Expect <cmd>:#,#,#
        toks  = epics_response.decode().split(':')
        res = toks[1].replace("\x00","").strip().split(',')
        integer_list = [int(x) for x in res]        
        return integer_list
        
    #
    # Wait for acquire and Save to complete
    #
    def waitForAcquireAndSave(self, timeout_sec = 100):
        
        maxTime = timeout_sec
       
        while maxTime>0:
            res = self.queryAcqStatus()
            if len(res) != 3:
                return (-1) # Error out
            
            acquiringStatus = res[0]
    
            if acquiringStatus ==  0:
                saveStatus  = res[1]
                nFramesLeft = res[2]   
                if nFramesLeft <= 0:
                    break
            time.sleep(.5)
            maxTime -= .5
        
        return (0) # success            



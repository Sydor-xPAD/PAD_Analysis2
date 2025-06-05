#!/usr/bin/env python3
#

# YF 21MAY2024 - Simulate TXC artifacts

import numpy as np
import matplotlib.pyplot as plt

class bouncyball:
    def __init__(self) -> None:
        self.x = 15
        self.y = 15
        self.vx = 0/34.0
        self.vy = 0/34
        self.dint = 4/34.0
        self.int = 1
        
    def tick(self):
        if (self.x + self.vx > 31) or (self.x < 0):
            self.vx=-self.vx

        if (self.y + self.vy > 31) or (self.y <0 ):
            self.vy=-self.vy

        self.x += self.vx   
        self.y += self.vy
        self.int += self.dint
        
        print(f"I xy:{self.int}  {self.x},{self.y}")
                 
    
#
#
#
#   
class TXC_Sim:
    def __init__(self) -> None:
        nFrames = 34
        nWidth = 32
        nHeight = 32
        self.frame = np.zeros( (nFrames, nWidth), dtype = np.int32) 
        self.sim = np.zeros( (nHeight, nWidth), dtype = np.int32)
        self.image = np.zeros( (nHeight, nWidth), dtype = np.int32) 
        self.bb = bouncyball()
    
    def create_sim(self):
        
        #
        # 1 single hot pixel in the center
        for iy in range(32):
            for ix in range(32):
                self.sim[iy,ix] = self.bb.int if  abs(ix - self.bb.x) <= 2 \
                    and  abs( iy - self.bb.y ) <= 1  else 0
        
        
    def tick(self):
        """
        Move the simulated spot in time
        """
        self.bb.tick()
        self.create_sim()
        
        
    def calcImage(self):
        # frames 1-32 image, 33 is not used and 34 is 'All Off' 
        for nFrame in range(34):
            self.tick()
            for ix in range(32):
                self.frame[nFrame, ix]  = 0
                
                for ry in range(32):
                    s = 1 if ry == nFrame else -1
                    self.frame[nFrame, ix] += self.sim[ry,ix] * s


        for iy in range(32):
            for ix in range(32):
               self.image[iy,ix] = self.frame[iy,ix]  - self.frame[34-1, ix]
                    
if __name__ == "__main__":
    T = TXC_Sim()
    T.create_sim()
    T.calcImage()
    
    fig,ax = plt.subplots(1)

    image = ax.imshow( T.image, cmap = "viridis")
    cbar = fig.colorbar(image, aspect=10)
    ax.set_title('TXC Image')
    ax.set_ylabel("Pixel")
    ax.set_xlabel("Pixel")
    cbar.set_label ("Counts (ADU)")
    plt.show()

    
    
        

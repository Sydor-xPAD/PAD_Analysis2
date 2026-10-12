import numpy as np
import sys
import os
import inspect
import matplotlib.pyplot as plt
import matplotlib
import scipy
import math

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import padstack

def main(argv):
    imlist_filename = argv[0]   # The file containing the image files to read

    with open(imlist_filename, 'r', encoding='utf-8') as f:
        for line in f:
            im_filename = line.strip()
            #print(im_filename)

            curr_img = padstack.PADStack(im_filename, 'MMPAD')

            frame_idx = -1
            file_bad = False
            bad_voltage_other = False
            for meta in curr_img.metaStack:
                frame_idx += 1
                bad_voltage0 = False
                bad_voltage1 = False

                print(meta.__get__('v_low_asic0'))
                
                if meta._get__('v_low_asic0')[0] > 2:
                    bad_voltage0 = True
                    file_bad = True
                if meta.v_low_asic1[0] > 2:
                    bad_voltage1 = True
                    file_bad = True

                
                for v_idx in range(7):
                    if (meta.v_low_asic0[v_idx+1] > 2) or (meta.v_low_asic1[v_idx+1] > 2):
                        bad_voltage_other = True
                        print(meta.v_low_asic0)
                        print(meta.v_low_asic1)
                        break

                

                if bad_voltage0:
                    print("{}:{}:Vlow0 high".format(im_filename,frame_idx))
                if bad_voltage1:
                    print("{}:{}:Vlow1 high".format(im_filename,frame_idx))

            if not file_bad:
                print("Good: {}".format(im_filename))
            else:
                print("Bad: {}".format(im_filename))

            if bad_voltage_other:
                print("Other: {}".format(im_filename))
            #print(curr_img.metaStack[0].v_low_asic0)
            #print(curr_img.metaStack[0].v_low_asic1)
            
    sys.exit(0)

if __name__ == '__main__':
    main(sys.argv[1:])

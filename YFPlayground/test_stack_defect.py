import padstack
import sys
import copy
import struct
import math

fg_file = sys.argv[1]
bg_file = sys.argv[2]
ff_file = sys.argv[3]
defect_file = sys.argv[4]
gc_file = sys.argv[5]
sys_type = sys.argv[6]

my_stack = padstack.PADStack(fg_file, sys_type)
my_bg = padstack.PADStack(bg_file, sys_type)

print("Cap Mask: 0x{:03x}".format(my_stack.capMask))
print("Num Images: {}".format(my_stack.numImages))
print("Num Caps: {}".format(my_stack.numCaps))
print("Image Size: {}".format(my_stack.imgSize))

back_stack = copy.copy(my_bg)
back_stack.computeBgStack()

numCaps = back_stack.numImages
#out_file = open("test_bgsub.raw", 'wb')

my_stack.bgSub(back_stack)
print("BG Sub done.")
#for frameIdx in range(my_stack.numImages):
#    for rowIdx in range(my_stack.imgSize[0]):
#        for colIdx in range(my_stack.imgSize[1]):
#            curr_pix = int(my_stack.imgStack[frameIdx][rowIdx,colIdx]) & 0xffff;
#            out_bytes = struct.pack('<H', curr_pix)
#            out_file.write(out_bytes)



my_defect = padstack.PADStack(defect_file, sys_type, 'DEFECT')
my_stack.applyDefect(my_defect)

#out_file.close()

# Now do flatfield calculations
my_ff = padstack.PADStack(ff_file, sys_type, 'FF')
#my_stack.applyFF(my_ff)
#out_file = open("test_ff.raw", 'wb')

for frameIdx in range(my_stack.numImages):
    out_bytes = b''
#    my_stack.imgStack[frameIdx].tofile(out_file);
    #for rowIdx in range(my_stack.imgSize[0]):
    #    for colIdx in range(my_stack.imgSize[1]):
    #        curr_pix = float(my_stack.imgStack[frameIdx][rowIdx,colIdx])
    #        out_bytes = out_bytes + struct.pack('<d', curr_pix)
    #out_file.write(out_bytes)

#out_file.close()

my_stack.apply_debounce()

my_stack.nan_pad()
my_stack.nan_filter()
my_stack.geocorr(gc_file)
out_file = open("test_db.raw", 'wb')

for frameIdx in range(my_stack.numImages):
    out_bytes = b''
    my_stack.imgStack[frameIdx].tofile(out_file);
    #for rowIdx in range(my_stack.imgSize[0]):
    #    for colIdx in range(my_stack.imgSize[1]):
    #        curr_pix = float(my_stack.imgStack[frameIdx][rowIdx,colIdx])
    #        out_bytes = out_bytes + struct.pack('<d', curr_pix)
    #out_file.write(out_bytes)

out_file.close()


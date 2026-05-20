import padstack
import sys
import copy
import struct

fg_file = sys.argv[1]
bg_file = sys.argv[2]
sys_type = sys.argv[3]

my_stack = padstack.PADStack(fg_file, sys_type)
my_bg = padstack.PADStack(bg_file, sys_type)

print("Cap Mask: 0x{:03x}".format(my_stack.capMask))
print("Num Images: {}".format(my_stack.numImages))
print("Num Caps: {}".format(my_stack.numCaps))
print("Image Size: {}".format(my_stack.imgSize))

back_stack = copy.copy(my_bg)
back_stack.computeBgStack()

numCaps = back_stack.numImages
out_file = open("test_bgsub.raw", 'wb')

my_stack.bgSub(back_stack)
for frameIdx in range(my_stack.numImages):
    for rowIdx in range(my_stack.imgSize[0]):
        for colIdx in range(my_stack.imgSize[1]):
            curr_pix = int(my_stack.imgStack[frameIdx][rowIdx,colIdx]) & 0xffff;
            out_bytes = struct.pack('<H', curr_pix)
            out_file.write(out_bytes)

out_file.close()

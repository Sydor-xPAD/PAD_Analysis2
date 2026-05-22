import sys
import math

class GC_Line:
    def __init__(self, line):
        self.split_line = line.split(',')
        self.shift_x = 0
        self.shift_y = 0
        self.shift_theta = 0
        self.gx = float(self.split_line[4].strip())
        self.gy = float(self.split_line[5].strip())
        self.theta = float(self.split_line[3].strip())
        
    def print_update(self):
        self.split_line[3] = '{:8.3f}'.format(self.shift_theta*57.295)
        self.split_line[4] = '{:8.3f}'.format(self.shift_x)
        self.split_line[5] = '{:8.3f}'.format(self.shift_y)
        print(','.join(self.split_line))

def rotate_center(point, center, theta):
    shift_point = (point[0]-center[0],point[1]-center[1])
    out_x = shift_point[0]*math.cos(theta)+shift_point[1]*math.sin(theta)+center[0]
    out_y = -shift_point[0]*math.sin(theta)+shift_point[1]*math.cos(theta)+center[1]
    return (out_x, out_y)
        
in_filename = sys.argv[1]
center_point_yx = (624/2, 532/2)
center_point = (center_point_yx[1], center_point_yx[0])

# Read in all the gc line
in_file = open(in_filename, 'r')

gc_list = []
for line in in_file:
    if line.startswith("#"):
        continue

    curr_gc = GC_Line(line)
    gc_list.append(curr_gc)

in_file.close()

# Compute the overall rotation
total_theta = 0
for gc in gc_list:
    total_theta += gc.theta

overall_theta = total_theta / len(gc_list)/180*math.pi
adj_theta = overall_theta      # Adjust in opposite direction -- Nope

#-=-= DEBUGGING
print("Adjust theta: {}".format(adj_theta*180/math.pi))

# Now rotate each of the submodules and compute its new angle
geo_offset_x = 9999
geo_offset_y = 9999 # These numbers are bigger than the maximum values we would see
for gc in gc_list:
    # Get the current corner points
    gx = gc.gx
    gy = gc.gy
    theta = gc.theta
    base_pos = (gx, gy)

    # Compute an extended point along its angle
    ex = gx+math.cos(theta/180*math.pi)
    ey = gy+math.sin(theta/180*math.pi)
    ext_pos = (ex, ey)

    # Rotate both points
    base_rot = rotate_center(base_pos, center_point, adj_theta)
    ext_rot = rotate_center(ext_pos, center_point, adj_theta)

    print("********")
    print(base_rot)
    print(ext_rot)
    print((ext_rot[0]-base_rot[0], ext_rot[1]-base_rot[1]))
    # Compute new angle
    new_angle = math.atan2(ext_rot[1]-base_rot[1], ext_rot[0]-base_rot[0])
    print((theta, new_angle))
    gc.shift_theta = new_angle
    gc.shift_x = base_rot[0]
    gc.shift_y = base_rot[1]

    # Update the smallest shift we see
    if gc.shift_x < geo_offset_x:
        geo_offset_x = gc.shift_x

    if gc.shift_y < geo_offset_y:
        geo_offset_y = gc.shift_y

# Now adjust all of the offsets
for gc in gc_list:
    gc.shift_x = gc.shift_x - geo_offset_x +2
    gc.shift_y = gc.shift_y - geo_offset_y +2

# Now print out the geocal
for gc in gc_list:
    gc.print_update()

# Counts the peaks in each submodule of a peak-detected image

import numpy as np
import Big_keck_load as BKL
import scipy
import scipy.ndimage as ndimage
import scipy.ndimage.filters as filters
from scipy.optimize import minimize
import imageio
import os
import matplotlib
import matplotlib.pyplot as plt
import sys
import tkinter.filedialog as fd
#import findpeaks.findpeaks as fp   # https://erdogant.github.io/findpeaks/pages/html/index.html 
import tifffile
import math
import copy

ASIC_HEIGHT = 128
ASIC_WIDTH  = 128

PEAKS_EXPECTED = 81

## A named structure for geocal parameters
class AsicCorrections:
    ## Default constructor
    def __init__(self, params):
        self.length = params[0]
        self.delta = params[1]
        self.scale = params[2]
        self.theta = params[3]
        self.center = (params[4], params[5])
        self.sq_err = 0; # Error in the fitting

    ## Gets the grid fit parameters as a list
    def get_fit_list(self):
        return [self.scale, self.theta, self.center[0], self.center[1]]

## Holds the details of a submodule, created from two ASICs
class Submodule:
    ## Default constructor
    #
    #  @param asic_left -- Corrections for left ASIC
    #  @param asic_right -- Corrections for right ASIC
    def __init__(self, asic_left, asic_right):
        self.corr_left = copy.deepcopy(asic_left)
        self.corr_right = copy.deepcopy(asic_right)
        self.total_err = abs(self.corr_left.sq_err) + abs(self.corr_right.sq_err)
        self.avg_mag = (self.corr_left.scale + self.corr_right.scale)/2.0
        self.avg_theta = -(self.corr_left.theta + self.corr_right.theta)/2.0 # Negative to apply correction in output
        self.left_delta = (-1234, -1234)
        self.right_delta = (-1234, -1234) # Difference from center of ASIC
        self.local_x = [-1234, -1234]     # Local X center coordinates for left, right
        self.local_y = [-1234, -1234]     # Local Y center coordinates for left, right
        self.rot_x = [-1234, -1234]       # Rotated local X center coordinates for left, right
        self.rot_y = [-1234, -1234]       # Rotated local Y center coordinates for left, right
        self.ADDED_PIXELS = 130           # Pixels after center expansion
        self.PIXEL_SHIFT = 3              # Pixels added during shift

    ## Compute difference between peak center and ASIC center
    #
    #  @param left_ctr Tuple of (y,x) of left ASIC center
    #  @param right_ctr Tuple of (y,x) of right ASIC center
    def calc_delta(self, left_ctr, right_ctr):
        self.left_delta = (self.corr_left.center[0]-left_ctr[0], self.corr_left.center[1]-left_ctr[1])
        self.right_delta = (self.corr_right.center[0]-right_ctr[0], self.corr_right.center[1]-right_ctr[1])


    ## Compute the local co-ordinates of centers and the rotated variants thereof
    # @param asic_height The height of the ASIC
    # @param asic_width The width of the ASIC
    def calc_centers(self, asic_height, asic_width):
        self.ASIC_HEIGHT = asic_height
        self.ASIC_WIDTH = asic_width

        self.local_x[0] = self.left_delta[1] + asic_width/2
        self.local_y[0] = self.left_delta[0] + asic_height/2

        self.local_x[1] = self.right_delta[1] + asic_width/2 + self.ADDED_PIXELS
        self.local_y[1] = self.right_delta[0] + asic_height/2
                     
        full_width = asic_width*2 + self.PIXEL_SHIFT
        full_center_x = full_width/2.0;
        full_center_y = float(asic_height/2);

        for ctr_idx in range(2):
            x = self.local_x[ctr_idx] - full_center_x
            y = self.local_y[ctr_idx] - full_center_y

            self.rot_x[ctr_idx] = x * math.cos(self.avg_theta) - y * math.sin(self.avg_theta) + full_center_x
            self.rot_y[ctr_idx] = x * math.sin(self.avg_theta) + y * math.cos(self.avg_theta) + full_center_y
        
## Generates a square grid of points
#
# @param length    How many points on a side
# @param delta     The nominal number of pixels between peaks on the mask
# @param scale     The scaling factor to apply to the grid spacing
# @param theta     The rotation clockwise in radians - Clockwise since Y goes down
# @param offset    The offset of the grid, specified as (y,x)
# @return List of (LENGTH^2) tuples of (row, col) on success, None on failure
def gen_grid(length, delta, scale, theta, offset=(0,0)):
    length = int(length)
    if length%2 == 0:
        print("Length must be odd.")
        return None

    mid_val = length/2+1;     # Get the value in the middle of the length

    grid_points = [];
    for row_idx in range(length):
        row_val = row_idx-mid_val+1 # Row number centered around mid_val for interval [-length/2, length/2]
        row_dist = row_val*delta*scale # Expand to a distance per row
        for col_idx in range(length):
            col_val = col_idx-mid_val+1 # Column number the same way as rows above
            col_dist = col_val*delta*scale # Distance as above

            rot_col = math.cos(theta)*col_dist - math.sin(theta)*row_dist+offset[1] 
            rot_row = math.sin(theta)*col_dist + math.cos(theta)*row_dist+offset[0] # Rotation matrix plus offset
            grid_points.append((rot_row, rot_col))

    return grid_points

## Peak_Image
#
#  Holds details of an image of peaks for geocalibration
class Peak_Image:
    ## Constructor
    #
    #  @return Object with default values
    def __init__(self):
        self.ASIC_HEIGHT = 128    ##< The height of an ASIC in pixels
        self.ASIC_WIDTH = 128     ##< The width of an ASIC in pixels
        self.PEAKS_EXPECTED = 81  ##< The number of points in the mask pattern
        self.LENGTH = 9           ##< The number of points on a side of the mask pattern
        self.NUM_COLS = 4         ##< The number of columns of ASICs
        self.NUM_ROWS = 4         ##< The number of rows of ASICS
        self.peak_img = None      ##< The image of peaks
        self.neighbor_mask = np.array([[1,1,1],[1,1,1],[1,1,1]]); ##< The mask to force 8-connection in the neighborhood labeling
        self.labeled_img = None   ##< The peak image with the peaks uniquely labels
        self.num_objects = 0
        self.CoM = None           ##< The center of mass for some calculations.  (row, col)
        self.DELTA = 11           ##< The nominal spacing in pixels between peaks from the mask
        self.asic_com = None      ##< A list of CoM in a specified ASIC, in order from top-left to bottom right
        self.center_delta = (-self.ASIC_WIDTH, -self.ASIC_HEIGHT); # X,Y of how far the center is from the nominal center of an ASIC -=-= FIXME Maybe change co-ordinates
        return

    ## Sets the image member
    #  @param newImage The image to store -=-= XXX Hopefully a deep copy
    #  @return None
    def set_image(self, newImage):
        self.peak_img = newImage + 0; # Try to enforce a deep copy

        return

    ## Label the peaks of the image member
    #
    #  Labels the internal image with neighbors determined by neighbor mask member.
    #  @return None if no image set.  True if image set.
    def label_peaks(self):
        if self.peak_img is None:
            return None

        labeled_img, num_objects = ndimage.label(self.peak_img, structure=self.neighbor_mask)
        self.labeled_img = labeled_img
        self.num_objects = num_objects

        return True

    ## Count the peaks in all the ASICs to verify correct number
    #
    #  @return False if image not set, no background found, or incorrect number of peaks found.  True on success.
    def quadrant_peak_count(self):
        if self.peak_img is None:
            return None

        for row_idx in range(self.NUM_ROWS):
            for col_idx in range(self.NUM_COLS):
                start_row = self.ASIC_HEIGHT * row_idx
                start_col = self.ASIC_WIDTH * col_idx
                end_row = start_row + self.ASIC_HEIGHT
                end_col = start_col + self.ASIC_WIDTH
                curr_asic_pix = self.labeled_img[start_row:end_row,start_col:end_col]
                distinct_val = set(curr_asic_pix.flat)
                if not 0 in distinct_val:
                    print("ERROR: No background found in ASIC {},{}".format(row_idx, col_idx));
                    return False
                
                num_peaks = len(distinct_val - set([0]));
                print("ASIC {},{} has {} peaks.".format(row_idx, col_idx, num_peaks))
                if (num_peaks != self.PEAKS_EXPECTED):
                    print("Error: Incorrect number of peaks.  Wanted: {} Actual: {}".format(self.PEAKS_EXPECTED, num_peaks))
                    return False
        return True

    ## Compute the centers of mass
    #
    #  Computes a list of centers of mass for all peaks.  Run after label_peaks()
    #  @return Always succeeds.
    def calc_CoM(self):
        self.CoM = ndimage.center_of_mass(self.peak_img, labels=self.labeled_img, index=list(set(self.labeled_img.flat)-set([0]))) # Get every unique peak and subtract out the CoM for 0, where there is no peak

    ## Determine if a point is an a specificed ASIC
    #
    #  @param test_point (row,col) of the point to test
    #  @param asic_idx (asic row, asic_col) of the ASIC selected
    #  @return True if point in ASIC, False if not
    def point_in_asic(self, test_point, asic_idx):
        start_row = self.ASIC_HEIGHT * asic_idx[0]
        start_col = self.ASIC_WIDTH * asic_idx[1]
        end_row = start_row + self.ASIC_HEIGHT
        end_col = start_col + self.ASIC_WIDTH

        if (test_point[0] >= start_row) and (test_point[0] < end_row):
            if (test_point[1] >= start_col) and (test_point[1] < end_col):
                return True

        return False

    ## Determine CoMs in a specified ASIC
    #
    #  @param asic_idx (asic row, asic col) to extract CoMs from
    #  @return List of (row, col) tuples of CoMs in the specfied ASIC
    def com_in_asic(self, asic_idx):
        CoM = [];
        
        for curr_peak in self.CoM:
            if self.point_in_asic(curr_peak, asic_idx):
                CoM.append(curr_peak)

        return CoM

    ## Compute square distance between to points
    #
    #  -=-= FIXME check order of points in tuples
    #  @param point1 (col,row) tuple of first point
    #  @param point2 (col,row) tuple of second point
    #  @return Square of distance between point1 and point2
    def point_dist_sq(self, point1, point2):
        delta_x = point1[0] - point2[0]
        delta_y = point1[1] - point2[1]
        
        return (delta_x*delta_x + delta_y*delta_y)

    ## Find nearest CoM to a point
    #
    #  @param point (row,col) tuple of point being tested
    #  @param List of (row,col) tuples of CoMs to find nearest
    #  @return (Index, Squared Distance) of CoM in list that is closed to point
    def nearest_com(self, point, com_list):

        # Initialize with first point
        curr_point = com_list[0]
        curr_dist_sq = self.point_dist_sq(curr_point, point)
        min_dist_sq = curr_dist_sq
        min_idx = 0
        
        for point_idx in range(len(com_list)):
            curr_point = com_list[point_idx]
            curr_dist_sq = self.point_dist_sq(curr_point, point)
            if (curr_dist_sq < min_dist_sq):
                min_dist_sq = curr_dist_sq
                min_idx = point_idx

        return min_idx, min_dist_sq

    ## Find nearest CoM to a point
    #
    #  @param point (row,col) tuple of point being tested
    #  @param List of (row,col) tuples of CoMs to find nearest
    #  @return (row, col) of CoM in list that is closed to point
    def nearest_com_point(self, point, com_list):
        min_idx, min_distsq = self.nearest_com(point, com_list)
        return com_list[min_idx]

    ## Get ordered list of CoMs in a specified ASIC
    #
    #  @param row The row of the ASIC
    #  @param col The column of the ASIC
    #  Sets member list of CoMs in order from Top-Left to Bottom-Right
    #  @return Always returns True
    def set_asic(self, row, col):
        asic_com = self.com_in_asic((row, col)) # Create a list of centers of mass
        # -=-= DEBUGGING
        #print("Raw ASIC COM")
        #print(len(asic_com))
        #print(asic_com)
        # Compute the center point of the grid to place the generated grid
        avg_row = 0
        avg_col = 0
        point_count = 0.0
        for curr_point in asic_com:
            avg_row += curr_point[0]
            avg_col += curr_point[1]
            point_count += 1.0
        avg_row = avg_row / point_count
        avg_col = avg_col / point_count

        # -=-= DEBUGGING
        #print("Nominal center: {}, {}".format(avg_row, avg_col))
        # Find the actual starting position
        center_pos_a = self.nearest_com_point((avg_row, avg_col), asic_com)
        # -=-= DEBUGGING
        #print("Actual center: {}, {}".format(center_pos_a[0], center_pos_a[1]))

        y_grid_center = row*self.ASIC_HEIGHT + self.ASIC_HEIGHT/2
        x_grid_center = col*self.ASIC_WIDTH + self.ASIC_WIDTH/2

        # Now walk our way to the left
        half_walk_limit = int(self.LENGTH/2)
        curr_found_point = center_pos_a; # Start from the center
        for col_idx in range(half_walk_limit):
            curr_test_point = (curr_found_point[0], curr_found_point[1]-self.DELTA); # Adjust self.DELTA to the left
            curr_found_point = self.nearest_com_point(curr_test_point, asic_com) # Update the point with the newest

        # Walk upwards
        for row_idx in range(half_walk_limit):
            curr_test_point = (curr_found_point[0]-self.DELTA, curr_found_point[1]); # Walk upwards
            curr_found_point = self.nearest_com_point(curr_test_point, asic_com)

        # We should now have the top-left point found
        print("Grid top-left is: {}".format(curr_found_point))

        # Prepare some bookkeeping variable
        self.asic_com = []      # Empty list
        row_start_point = curr_found_point # We need to refer to the start of the row after doing all columns
        curr_iter_point = curr_found_point # The point we use in iteration
        curr_com_point = curr_found_point  # The point we store the nearest in
    
        for row_idx in range(self.LENGTH):
            for col_idx in range(self.LENGTH):
                curr_com_point = self.nearest_com_point(curr_iter_point, asic_com); # Compute the nearest
                self.asic_com.append(curr_com_point) # Add to the list
                # -=-= DEBUGGING
                #print(curr_com_point)
                curr_iter_point = (curr_com_point[0], curr_com_point[1]+self.DELTA); # Walk right one point
            # To prepare for the next row
            curr_iter_point = (row_start_point[0]+self.DELTA, row_start_point[1]) # Go to the start of the row, then walk down one point
            curr_com_point = self.nearest_com_point(curr_iter_point, asic_com) # Compute nearest
            row_start_point = curr_com_point # Update row value for next row
            curr_iter_point = curr_com_point # Store value for next iteration
                
                                 
        return True

    ## Calculate the total distance of points in a generated grid to the peaks in an ASIC
    #
    # Assume that the internal CoM list has been set with set_asic
    # @param grid_coeff grid_coeff is an array with scale, theta, offset_row, offset_col
    # @return Total distance
    def calc_err(self, grid_coeff):
        # First generate the grid we are fitting
        curr_grid = gen_grid(self.LENGTH, self.DELTA, grid_coeff[0], grid_coeff[1], (grid_coeff[2], grid_coeff[3]))

        # Evaluate distance**2 for each point in generated grid to its match in the mask
        total_dist = 0.0
        # -=-= DEBUGGING
        #print("##############")
        #print(len(curr_grid))
        for curr_idx in range(len(curr_grid)):
            curr_point = curr_grid[curr_idx]
            curr_com = self.asic_com[curr_idx]
            # -=-= DEBUGGING
            #print("{},{}".format(curr_point, curr_com))
            min_dist = self.point_dist_sq(curr_point, curr_com)
            total_dist += math.sqrt(min_dist)

        return total_dist

    #-=-= NOTE Do not use; a scale of zero in grid_coeff will have zero error but be totally wrong.
    # Assume that the internal CoM list has been set with set_asic
    # grid_coeff is an array with scale, theta, offset_row, offset_col
    def calc_err_unorder(self, grid_coeff):
        # First generate the grid we are fitting
        curr_grid = gen_grid(self.LENGTH, self.DELTA, grid_coeff[0], grid_coeff[1], (grid_coeff[2], grid_coeff[3]))

        # Evaluate distance**2 for each point in generated grid to its match in the mask
        total_dist = 0.0

        for curr_point in curr_grid:
            min_idx, min_dist = self.nearest_com(curr_point, self.asic_com)
            total_dist += math.sqrt(min_dist)

        return total_dist

    # Do not use
    # Assume that the internal CoM list has been set with set_asic
    # Grid coeff is an array with theta, offset_row, offset_col
    def calc_err2(self, grid_coeff):
        # First generate the grid we are fitting
        curr_grid = gen_grid(self.LENGTH, self.DELTA, 1.0, grid_coeff[0], (grid_coeff[1], grid_coeff[2]))

        # Evaluate distance**2 for each point in generated grid
        total_dist = 0.0
        for curr_point in curr_grid:
            min_idx, min_dist = self.nearest_com(curr_point, self.asic_com)
            total_dist += math.sqrt(min_dist)

        return total_dist

# Set some of the geometric parameters
delta_x_geo = [-(20.23/2 + 19.62) , (20.23/2)] # Distances in millimeters
delta_y_geo = [-(22 + 23.6/2.0), -(23.6/2.0), (23.6/2.0), (22 + 23.6/2.0)] # Distances in millimeters
    
# The path of the peak-detected image
maskPath = "xpad_corrections/geocal_full_mask.tiff"

# Read in the image
data = imageio.imread(maskPath)
#-=-= Changed file
data = imageio.imread("xpad_corrections/geocal_full_mask.tiff")

print("Image Shape: {}".format(data.shape))
print("Image Type: {}".format(data.dtype))

# Initialize the peak image object.
geocal_img = Peak_Image()

geocal_img.set_image(data)

if not geocal_img.label_peaks():
    print("Error labeling peaks.")
    sys.exit(1)

peak_count_status = geocal_img.quadrant_peak_count()
if peak_count_status is None:
    print("No image for peak counting.")
    sys.exit(1)
elif peak_count_status is False:
    print("Error in peak count.")
    sys.exit(1)
else:
    pass

# With the image labeled, I can check the center of mass

geocal_img.calc_CoM();

for row_idx in range(4):
    for col_idx in range(4):
        com_list = geocal_img.com_in_asic((row_idx, col_idx))
        print("ASIC {},{} has {} CoM.".format(row_idx, col_idx, len(com_list)))


test_nearest = (403,134)
my_com_list = geocal_img.com_in_asic((3,1))
com_idx, com_dist_sq = geocal_img.nearest_com(test_nearest, my_com_list)
print("Nearest CoM to {},{} is {},{}.".format(test_nearest[0], test_nearest[1], my_com_list[com_idx][0], my_com_list[com_idx][1]));

# Plot rotated grid

my_grid = gen_grid(9, 11, 1, 10.0/180*3.141593, offset=(448,192))
my_grid = gen_grid(9, 11, 1, 0, offset=(448,192))
#for point in my_grid:
#    geocal_img.peak_img[int(point[0]),int(point[1])] = 200

#plt.imshow(geocal_img.peak_img)
#plt.show()

# Now try the minimization
geocal_img.set_asic(3,0)
res1 = minimize(geocal_img.calc_err, [1.0, 0, 448, 64], method='nelder-mead')

# -=-= DEBUGGING
#print(res1.x)
res1_x = res1.x
my_grid = gen_grid(9, 11, res1_x[0], res1_x[1], offset=(res1_x[2], res1_x[3]))


# -=-= DEBUGGING
#print("CoM points:")
#print(geocal_img.asic_com)

# Try iterating over every asic
full_grid = [];  # A list of all found peaks over the full array
asic_ctr = [];
asic_grid = [];  # A list of peaks for each ASIC
asic_fit_info = [];
for asic_row in range(4):
    for asic_col in range(4):
        geocal_img.set_asic(asic_row, asic_col)
        res1 = minimize(geocal_img.calc_err, [1.0, 0, asic_row*128.0 + 0.5*128, asic_col*128.0+0.5*128], method='nelder-mead')
        #print(res1)
        res1_x = res1.x
        my_grid = gen_grid(9, 11, res1_x[0], res1_x[1], offset=(res1_x[2], res1_x[3]))
        curr_correction = AsicCorrections([9, 11, res1_x[0], res1_x[1], res1_x[2], res1_x[3]]);
        curr_correction.sq_err = res1.fun
        asic_fit_info.append(curr_correction)
        full_grid.extend(my_grid)
        asic_grid.append(my_grid)


sm_list = []
for sm_idx in range(8):
    curr_submodule = Submodule(asic_fit_info[sm_idx*2], asic_fit_info[sm_idx*2+1])
    asic_row = int(sm_idx / 2)
    asic_col = (sm_idx % 2) * 2;
    sm_row = int(sm_idx /2)
    sm_col = sm_idx % 2
    nom_ctr_y =  asic_row * ASIC_HEIGHT + int(ASIC_HEIGHT/2); # Half-way down an ASIC
    nom_ctr_x_left = asic_col * ASIC_WIDTH + int(ASIC_WIDTH/2); # 2 ASICs across per submodule, plus half-way across an ASIC
    nom_ctr_x_right = nom_ctr_x_left + ASIC_WIDTH;             # One ASIC to the right of the of the one just calculated
    curr_submodule.calc_delta((nom_ctr_y, nom_ctr_x_left), (nom_ctr_y, nom_ctr_x_right))
    curr_submodule.calc_centers(ASIC_HEIGHT, ASIC_WIDTH)
    sm_list.append(curr_submodule)
    print("Submodule: {}".format(sm_idx))
    print("ASIC Selection: {}".format((asic_row, asic_col)))
    print("Nominal centers: Left {}\tRight: {}".format((nom_ctr_y, nom_ctr_x_left), (nom_ctr_y, nom_ctr_x_right)))
    print("ASIC Centers: Left: {}\tRight: {}".format(curr_submodule.corr_left.center, curr_submodule.corr_right.center))
    print("Center deltas: Left: {}\tRight: {}".format(curr_submodule.left_delta, curr_submodule.right_delta))
    print("Rotated local centers: Left: {}\tRight: {}".format((curr_submodule.rot_y[0], curr_submodule.rot_x[0]),(curr_submodule.rot_y[1], curr_submodule.rot_x[1])))

geo_offset_x = 9999             # Final result Much bigger than a full image for subtraction later
geo_offset_y = 9999             # Ibid
geoparams_filename = "geocal_python.txt"
geoparams_file = open(geoparams_filename, "w")
for pass_idx in range(2):
    for submodule_idx in range(8):
        sm_row = int(submodule_idx / 2)
        sm_col = int(submodule_idx % 2)
        asic_idx = int(submodule_idx * 2); # Two ASICs per submodule; grab the left ASIC
        pixel_size = 0.150;     # Pixel size in mm
        curr_sm = sm_list[submodule_idx]
        avg_mag = curr_sm.avg_mag
        avg_theta = curr_sm.avg_theta

        cx = avg_mag * (delta_x_geo[sm_col]) / pixel_size  - (curr_sm.rot_x[0] - ASIC_WIDTH/2);
        cy = avg_mag * (delta_y_geo[sm_row]) / pixel_size  - (curr_sm.rot_y[0] - ASIC_HEIGHT/2);
        gx = cx - ASIC_WIDTH/2
        gy = cy - ASIC_HEIGHT/2

        cxr = avg_mag * (delta_x_geo[sm_col]) / pixel_size  - (curr_sm.rot_x[1] - ASIC_WIDTH/2);
        cyr = avg_mag * (delta_y_geo[sm_row]) / pixel_size  - (curr_sm.rot_y[1] - ASIC_HEIGHT/2);
        if (pass_idx == 0):
            #-=-= DEBUGGING
            print('Centers: Left: ({:8.3f}, {:8.3f}) Right: ({:8.3f}, {:8.3f})'.format(cy,cx,cyr,cxr))
            if (gx < geo_offset_x):
                geo_offset_x = gx
            if (gy < geo_offset_y):
                geo_offset_y = gy
        else:
            gx = gx - geo_offset_x
            gy = gy - geo_offset_y
            correction_string = "{:d}, {:d}, {}, {:8.3f}, {:8.3f}, {:8.3f}, {:8.3f}, {:8.3f}, {:8.3f}, {:d}".format(submodule_idx, 160, "1A", avg_theta * 57.295, gx, gy, avg_mag, curr_sm.total_err, 0, 0)
            print(correction_string)
            geoparams_file.write(correction_string + "\n")
        
geoparams_file.close()
for point in full_grid:
    if (point[0] < 0) or (point[0] >= 512) or (point[1] < 0) or (point[1] >= 512):
        continue
    geocal_img.peak_img[int(point[0]),int(point[1])] = 200

print("Geocal Parameters")
for asic_idx in range(16):
    sm_num = int(asic_idx/2)
    print("{:3d} {:3d} Angle: {:5.3f} Mag: {:5.3f} Err: {:6.3f}".format(sm_num, asic_idx, asic_fit_info[asic_idx].theta * 180/3.141592, asic_fit_info[asic_idx].scale, asic_fit_info[asic_idx].sq_err))
    
#plt.imshow(geocal_img.peak_img)
#plt.show()


                               
sys.exit(0)
        
labeled_img, num_objects = ndimage.label(data, structure=neighbor_mask)


for row_idx in range(4):
    for col_idx in range(4):
        start_row = ASIC_HEIGHT * row_idx
        start_col = ASIC_WIDTH * col_idx
        end_row = start_row + ASIC_HEIGHT
        end_col = start_col + ASIC_WIDTH
        curr_asic = labeled_img[start_row:end_row,start_col:end_col]
        distinct_val = set(curr_asic.flat)
        if not 0 in distinct_val:
            print("ERROR: No background found in quadrant.");
        num_peaks = len(distinct_val - set([0]))
        print("ASIC ({},{}) has {} peaks.".format(row_idx, col_idx, num_peaks))
        if (num_peaks != PEAKS_EXPECTED):
            print("ERROR: Incorrect number of values.  Wanted: {} Actual: {}".format(PEAKS_EPECTED, num_peaks))

            
com_list = ndimage.center_of_mass(data, labels=labeled_img, index=list(set(labeled_img.flat)-set([0])))

for coords in com_list:
    data[int(coords[0]+0.5), int(coords[1]+0.5)] = 128;

plt.imshow(data)
plt.show()

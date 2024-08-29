import numpy as np
import math

##
# Holds several rasters and statistics to provide details of a simulated image sensor
class Image_Sensor:
    ## Constructor for an image object
    # @param self The object pointer
    # @param[in] img_size The size of the image
    # @param[in] sm_size The size of submodules/ASICs/etc that may have different characteristics
    def __init__(self, img_size, sm_size):
        self.img_size = img_size
        self.sm_size = sm_size
        self.compute_sm_sizes()

    ## Create a mask of lambdas for dark current
    # @param self The object pointer
    # @param[in] random_seed The seed used for the RNG
    # @param[in] dark_mean The average value of the dark current
    # @param[in] sm_sigma The std dev of dark mean over different submodules
    # @param[in] dark_sigma The std dev of dark current varying per pixel, as a fraction around a mean of 1
    def gen_dark_map(self, random_seed, dark_mean, sm_sigma, dark_sigma):
        self.dark_seed = random_seed
        self.dark_map = np.zeros(self.img_size)
        self.dark_sm_sigma = sm_sigma
        self.dark_sigma = dark_sigma
        self.dark_base_mean = dark_mean # Populate members with parameters
        self.dark_sm_mean = [] # Create a list to hold the mean of each submodule
        rng = np.random.default_rng(random_seed)
        
        # Compute the means for each submodule
        for row_idx in range(self.sm_dims[0]):
            for col_idx in range(self.sm_dims[1]):
                curr_mean = rng.normal(self.dark_base_mean, self.dark_sm_sigma)
                if (curr_mean < 0):
                    print("Warning: Dark current mean below zero.  Modifying.")
                    curr_mean = 1.0; # Clip to a fairly sensible value
                self.dark_sm_mean.append(curr_mean)

        # Now populate create the dark map
        for row_idx in range(self.sm_dims[0]):
            for col_idx in range(self.sm_dims[1]):
                # Retrieve the mean for the submodule
                curr_mean = self.dark_sm_mean[row_idx*self.sm_dims[1]+col_idx]
                # Compute the lambdas for the submodule
                curr_sm = rng.normal(1, self.dark_sigma, self.sm_size)
                start_x = col_idx*self.sm_size[1]
                start_y = row_idx*self.sm_size[0]
                #-=-= DEBUGING
                #print(start_y, start_x)
                #print(self.sm_size[0],self.sm_size[1])
                self.dark_map[start_y:(start_y+self.sm_size[0]),start_x:(start_x+self.sm_size[1])] = curr_sm*curr_mean

    ## Compute submodule numbers
    # @param self The object pointer
    def compute_sm_sizes(self):
        sm_dims = []; # Size of submodules

        for size_idx in range(2):
            sm_dims.append(int(self.img_size[size_idx]/self.sm_size[size_idx]))
            if (self.img_size[size_idx] % self.sm_size[size_idx]) != 0:
                raise ValueError

        self.sm_dims = (sm_dims[0], sm_dims[1])

    ## Compute a gain map that affects the signal-to-DN computation
    #
    # @param[in] random_seed The seed for generation
    # @param[in] sm_sigma The sigma of difference in gain between submodules
    # @param[in] base_sigma The sigma of difference in gain within a submodule
    def gen_gain_map(self, random_seed, sm_sigma, base_sigma):
        self.gain_seed = random_seed
        self.gain_map = np.zeros(self.img_size)
        self.gain_sm_sigma = sm_sigma
        self.gain_base_sigma = base_sigma # Populate members with parameters
        self.gain_sm_mean = [] # Create a list to hold the mean of each submodule

        rng = np.random.default_rng(random_seed)

        # Compute the means for each submodule
        for row_idx in range(self.sm_dims[0]):
            for col_idx in range(self.sm_dims[1]):
                curr_mean = rng.normal(1, self.gain_sm_sigma)
                if (curr_mean < 0):
                    print("Warning: Gain below zero.  Modifying.")
                    curr_mean = 1.0; # Set to some valid and obvious
                self.gain_sm_mean.append(curr_mean)

        # Now populate the gain map
        for row_idx in range(self.sm_dims[0]):
            for col_idx in range(self.sm_dims[1]):
                # Retrieve the mean for the submodule
                curr_mean = self.gain_sm_mean[row_idx*self.sm_dims[1]+col_idx]
                # Compute the gains for the submodule
                curr_sm = rng.normal(curr_mean, self.gain_base_sigma, self.sm_size)
                start_x = col_idx*self.sm_size[1]
                start_y = row_idx*self.sm_size[0]
                self.gain_map[start_y:(start_y+self.sm_size[0]),start_x:(start_x+self.sm_size[1])] = curr_sm;

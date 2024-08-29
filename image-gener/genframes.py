import numpy as np


##
# Holds a frame raster and metadata for a single frame.  Mulitple frames can be combined into an image
class Image_Frame:
    ##
    # @param self The object pointer
    # @param[in] random_seed The seed used for the RNG
    # @param[in] img_sensor The class describing the image sensor
    def __init__(self, random_seed, img_sensor):
        self.random_seed = random_seed
        self.img_sensor = img_sensor
        self.frame_type = "Unspecified Frame"
        self.frame_meta = {}

    ##
    # Creates a submodule-sized image
    # @param self The object pointer
    def gen_sm_raster(self):
        return nd.zeros(self.img_sensor.sm_size)

    ##
    # Get the coordinates of a given submodule
    # @param self The object pointer
    # @param[in] sm_coords The (row,col) of the submodule
    # @return ((y_start, y_end),(x_start, x_end))
    def get_sm_coords(self, sm_coords):
        start_coords = []
        end_coords = []
        for dim_idx in range(2):
            start_val = sm_coords[dim_idx]*self.img_sensor.sm_size[dim_idx]
            start_coords.append(start_val)
            end_coords.append(start_val+self.img_sensor.sm_size[dim_idx])
            
        return ((start_coords[0], end_coords[0]), (start_coords[1], end_coords[1]))

    ##
    # Gets the submodule index into a list from the submodule coordinates
    # @param self The object pointer
    # @param[in] sm_coords The coordinates of the submodule
    # @return The index of the submodule, or raises ValueError if out of range
    def get_sm_idx(self, sm_coords):
        for dim_idx in range(2):
            if (sm_coords[dim_idx] < 0) or (sm_coords[dim_idx] >= self.img_sensor.sm_dims[dim_idx]):
                raise ValueError

        return sm_coords[0]*self.img_sensor.sm_dims[1]+sm_coords[1]
    
    ##
    # Generates a dark frame using the map from the sensor
    def gen_dark_frame(self):
        rng = np.random.default_rng(self.random_seed) # Initialize the RNG

        # Create the dark image using the already-calculated lambdas
        self.img_array = rng.poisson(self.img_sensor.dark_map)
        self.frame_type = "Dark Frame"

        #-=-= DEBUGGING
        #print("Dark array std: {}".format(self.img_array.std()))
        return

    # Generates a frame based on an existing image
    def gen_frame_from_img(self, base_image):
        self.img_array = base_image+0;
        return
    
    
    
    # Generate frame from file
    def gen_frame_from_file(self, in_file):
        img_raster = np.fromfile(in_file, np.uint32, 512*512)
        reshape_raster = img_raster.reshape((512,512))
        self.img_array = reshape_raster


    ##
    # Generates a flatfield frame given a mean value
    # @param self The object pointer
    # @param[in] flat_mean The mean of the flatfield signal
    def gen_flat_frame(self, flat_mean):
        rng = np.random.default_rng(self.random_seed) # Initialize the RNG

        # Create a Poisson-distributed flatfield image
        self.img_array = rng.poisson(flat_mean, self.img_sensor.img_size)
        self.frame_type = "Flat Frame"
        return

    ##
    # Generates a frame with a single point
    # @param self The object pointer
    # @param point_val The value of the point
    def gen_point_frame(self, point_val):
        self.img_array = np.zeros(self.img_sensor.img_size)
        self.img_array[5,6] = point_val;
        self.frame_type = "Point Frame"
        return
    
##
    # Generates a flatfield frame given a mean value, plus rendering text
    # @param self The object pointer
    # @param[in] flat_mean The mean of the flatfield signal
    def gen_flat_text_frame(self, frame_num, flat_mean, start_row, base_message):
        rng = np.random.default_rng(self.random_seed) # Initialize the RNG

        # Create a Poisson-distributed flatfield image
        self.img_array = rng.poisson(flat_mean, self.img_sensor.img_size)

        # Add the text
        temp_image = cv.add(self.img_array, 0)
        cv.putText(temp_image, base_message + str(frame_num), (0, start_row), cv.FONT_HERSHEY_TRIPLEX, 0.5, 10000);

        self.img_array = np.asarray(temp_image)
        
        self.frame_type = "Text Frame"
        return

    
    ##
    # Generates an optionally Poisson-distributed frame given a base image
    # @param self The object pointer
    # @param[in] base_raster The raster for the base image
    # @param[in] apply_poisson True to distribute the data according to Poisson based on base_frame
    # @return Raises ValueError if image size doesn't match
    def gen_fg(self, base_raster, apply_poisson = True):
        if base_raster.shape != self.img_sensor.img_size:
            #-=-= DEBUGGING
            print("Image Size Mismatch.")
            print(base_raster.shape)
            print(self.img_sensor.img_size)
            raise ValueError

        if apply_poisson:
            rng = np.random.default_rng(self.random_seed) # Initialize the RNG
            self.img_array = rng.poisson(base_raster)     # Apply Poisson noise
            self.frame_type = "Poisson Image Frame"
        else:
            self.img_array = base_raster.copy()
            self.frame_type = "Copy Image Frame"

    ##
    # Creates a bounce frame for a sensor
    # @param self The object pointer
    # @param[in] bounce_range The upper and lower limits for a bounce
    def gen_bounce_frame(self, bounce_range):
        self.img_array = np.zeros(self.img_sensor.img_size)
        rng = np.random.default_rng(self.random_seed) # Initialize the RNG
        asic_bounce = [];

        for row_idx in range(self.img_sensor.sm_dims[0]):
            for col_idx in range(self.img_sensor.sm_dims[1]):
                sm_pix_range = self.get_sm_coords((row_idx, col_idx))
                curr_val = rng.uniform(bounce_range[0], bounce_range[1], 1)
                self.img_array[sm_pix_range[0][0]:sm_pix_range[0][1],sm_pix_range[1][0]:sm_pix_range[1][1]] = curr_val
                asic_bounce.append(curr_val)
                
        self.frame_meta['bounce_amount'] = asic_bounce
        self.frame_type = "Bounce Frame"

    ##
    # Adds a frame to this one
    # @param self The object pointer
    # @param[in] second_frame The frame to add
    # @return A new Image_Frame object that is a sum, or raise ValueError if size mismatch
    def add_frame(self, second_frame):
        if self.img_array.size != second_frame.img_array.size:
            raise ValueError
        
        new_frame = Image_Frame(self.random_seed, self.img_sensor) # Copy over some basic parameters
        new_frame.img_array = self.img_array + second_frame.img_array # Add frames
        new_frame.frame_type = "Add Frame" # Set new type
        new_frame.random_seed = -123456    # Set contrived seed

        return new_frame
        

    ##
    # Scale the frame in-place in the frame by a raster.
    # self.img_array is reallocated to account for casts.
    # @param self The object pointer
    # @param[in] scale_raster The raster to scale by
    # @return Nothing on success or raise ValueError if size mismatch
    def scale_frame(self, scale_raster):
        if self.img_array.size != scale_raster.size:
            raise ValueError

        # The type might change, so can't use *=
        self.img_array = self.img_array * scale_raster
        return
        

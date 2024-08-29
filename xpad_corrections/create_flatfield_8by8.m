#
# File: create_flatfield_8x8.m
# 2/29/24 - Load 8 backgrounds (1 CAP each)
# and 8 foregrounds (1 CAP each)
#
#
clear

cfg_filename = 'flatfield_map.ini';
#
#  ^Make sure to edit this file for Keck or MMPAD!
#

cfg_file = fopen(cfg_filename);
[cfg_list, file_status] = get_config_line(cfg_file);
fclose(cfg_file);

for cfg_idx = 1:size(cfg_list)(1)
  curr_name = strtrim(cfg_list{cfg_idx, 1}{1,1});
  curr_val = strtrim(cfg_list{cfg_idx, 2}{1,1});

  if strcmp(curr_name, "asic_width")
    asic_width = str2double(curr_val);
  elseif strcmp(curr_name, "asic_height")
    asic_height = str2double(curr_val);
  elseif strcmp(curr_name, "img_width")
    image_width = str2double(curr_val);
  elseif strcmp(curr_name, "img_height")
    image_height = str2double(curr_val);
  elseif strcmp(curr_name, "num_caps")
    num_caps = str2double(curr_val);
  elseif strcmp(curr_name, "file_offset")
    offset = str2double(curr_val);
  elseif strcmp(curr_name, "file_gap")
    gap = str2double(curr_val);
  elseif strcmp(curr_name, "num_skip_images")
    num_skip_images = str2double(curr_val);
  elseif strcmp(curr_name, "gain_threshold")
    gain_thresh = str2double(curr_val);
  elseif strcmp(curr_name, "dark_slope_thresh")
    bad_thresh = str2num(curr_val);
  elseif strcmp(curr_name, "x_margin")
    x_margin = str2double(curr_val);
  elseif strcmp(curr_name, "y_margin")
    y_margin = str2double(curr_val);
  elseif strcmp(curr_name, "dark_image_filename")
    dark_image_filename = curr_val;
  elseif strcmp(curr_name, "bright_image_filename")
    bright_image_filename = curr_val;
  elseif strcmp(curr_name, "dark_mask")
    dark_mask_filename = curr_val;
  elseif strcmp(curr_name, "hot_mask")
    hot_mask_filename = curr_val;
  elseif strcmp(curr_name, "bpp")
    sensor_bpp = str2double(curr_val);
  endif
endfor



#num_caps = 8;
#image_width = 512;
#image_height = 512;
#asic_width = 128;
#asic_height = 128;
#offset = 256;
#gap = 1024;
#num_skip_image = 0;             # The number of images at the start to skip
num_skip_frames = num_caps * num_skip_images; # Total frames to skip
#y_margin = 3;
#x_margin = 3;

asic_x_count = image_width/asic_width;
asic_y_count = image_height/asic_height;

asic_count = asic_x_count * asic_y_count;

num_iterations = 8;
##dark_raw_array = zeros(num_iterations, 512, 512); % Initialize a cell array to store the results
dark_raw_array = []
bright_raw_array = []

# new code
for cap=0:7
    cap_dark_image_filename = ...
       sprintf('/mnt/raid/keckpad/set-pre-chess-tests-1/run-run-ff_3ms_integ_100ns_interf_cap%d_bg/frames/run-ff_3ms_integ_100ns_interf_cap%d_bg_00000001.raw',cap,cap);
    #printf(    "%s\n", cap_dark_image_filename);
    #disp( cap_dark_image_filename );
        
    # /mnt/raid/keckpad/set-pre-chess-tests-1/run-run-ff_3ms_integ_100ns_interf_cap0_bg/frames/run-ff_3ms_integ_100ns_interf_cap0_bg_00000001.raw
    [dark_raw, num_dark_frames] = read_xpad_image(cap_dark_image_filename, sensor_bpp, ...
    offset, gap, image_width, image_height); #  , 10  );
    # The last value is an OPTIONAL MAX_FRAMES parameter, set it to
    # a small number for faster testing
    dark_raw_array = cat(3, dark_raw_array,dark_raw); % Store the result in the cell array
    
    printf("num_dark_frames = %d\n", num_dark_frames);
    
    
  # Skip the first NUM_SKIP_IMAGE images
  # Remember there are NUM_CAPS frames per image
#  if (num_skip_frames > 0)
#    disp("Skipping dark frames: ")
#    disp(num_skip_frames)
#    dark_raw_array(cap+1) = dark_raw_array(cap+1)(:,:,(num_skip_frames+1):num_dark_frames);

#  endif

endfor   
#num_dark_frames = num_dark_frames-num_skip_frames;
disp('Loaded dark image(s)')



## With the dark current image loaded, we can average the values per-cap
dark_image = avg_array_not_interspersed(dark_raw_array, 8);
# ^^ 8 is Number of CAPS

# doesnt work :-( imshow (dark_image(:,:,1) )
clear dark_raw 
disp('Averaged dark image') 



## Now repeat for the bright image
# new code
for cap=0:7
    cap_bright_image_filename = ...
       sprintf('/mnt/raid/keckpad/set-pre-chess-tests-1/run-ff_3ms_integ_100ns_interf_cap%d/frames/ff_3ms_integ_100ns_interf_cap%d_00000001.raw',cap,cap);
    #printf(    "%s\n", cap_dark_image_filename);
    disp( cap_bright_image_filename );
        
    # /mnt/raid/keckpad/set-pre-chess-tests-1/run-run-ff_3ms_integ_100ns_interf_cap0_bg/frames/run-ff_3ms_integ_100ns_interf_cap0_bg_00000001.raw
    [bright_raw, num_frames] = read_xpad_image(cap_bright_image_filename, sensor_bpp, offset, ...
    gap, image_width, image_height); # , 10  );
    # The last value is an OPTIONAL MAX_FRAMES parameter, set it to
    # a small number for faster testing
    bright_raw_array = cat(3, bright_raw_array,bright_raw); % Store the result in the cell array
    
    printf("num_bright_frames = %d\n", num_frames);
    
    
  # Skip the first NUM_SKIP_IMAGE images
  # Remember there are NUM_CAPS frames per image
#  if (num_skip_frames > 0)
#    disp("Skipping dark frames: ")
#    disp(num_skip_frames)
#    dark_raw_array(cap+1) = dark_raw_array(cap+1)(:,:,(num_skip_frames+1):num_dark_frames);

#  endif

endfor   

disp('Loaded bright image')
printf("Bright frames count: %i\n", num_frames);


## With the bright image loaded, we can average the values per-cap
bright_image = avg_array_not_interspersed(bright_raw_array, 8);
clear bright_raw
disp('Averaged bright image')
printf("Frames per cap: %i\n", num_frames/8);

## Now do the background subtraction
bg_sub_image = bright_image-dark_image;
disp('Completed background subtraction')

## We now need to NaN out the bad pixels.  These are contained in two PGM files
## Change the filenames here to suit.
bad_dark_pixels = imread(dark_mask_filename);
bad_hot_pixels = imread(hot_mask_filename);
disp('Loaded bad pixel maps')

## -=-= XXX Makes no accounting for overflow of the sum, so the masks should only have values of 1
bad_pixels = bad_dark_pixels+bad_hot_pixels; #Combine the two images
bad_pixel_loc = find(bad_pixels != 0);       #Get the locations
disp('Found bad pixels')

## Set all bad flat pixels to NaN
## Iterate over all caps
for cap_idx = 1:num_caps
  curr_slice = bg_sub_image(:,:,cap_idx);
  curr_slice(bad_pixel_loc) = NaN;
  bg_sub_image(:,:,cap_idx) = curr_slice;
  disp('Masked bad pixels for cap ')
  cap_idx
endfor

## Now compute the flatfield corrections
flat_raster = zeros(image_height, image_width, num_caps);

pix_std = zeros(asic_count, num_caps);
pix_mean = zeros(asic_count, num_caps);         # -=-= TODO Make generic
for cap_idx = 1:num_caps
  curr_frame = bg_sub_image(:,:,cap_idx);
  # Second parameter below is the threshold of gain deemed too low.
  flat_raster(:,:,cap_idx) = calc_flat_asic(curr_frame, gain_thresh);

  asic_idx = 0;
  for row_idx=1:asic_y_count
    row_lower = (row_idx-1)*asic_height+1;
    row_upper = row_lower+asic_height - 1;
    row_lower = row_lower + y_margin;
    row_upper = row_upper - y_margin;

    for col_idx=1:asic_x_count
      col_lower = (col_idx-1)*asic_width+1;
      col_upper = col_lower+asic_width - 1;
      col_lower = col_lower + x_margin;
      col_upper = col_upper - x_margin;

      asic_idx = asic_idx + 1;

      curr_asic_pix = curr_frame(row_lower:row_upper, col_lower:col_upper);
      curr_flat_asic = flat_raster(row_lower:row_upper,col_lower:col_upper,cap_idx);
      curr_flat_asic = reshape(curr_flat_asic, 1, []);
      curr_flat_asic = curr_flat_asic(find(isfinite(curr_flat_asic)));
      flat_pix = reshape(calc_flat_asic(curr_asic_pix, gain_thresh),1, []);
      flat_pix = flat_pix(find(isfinite(flat_pix)));
      if isempty(flat_pix)
        pix_std(asic_idx, cap_idx) = NaN;
        pix_mean(asic_idx, cap_idx) = NaN;          # This should be an invalid value
      else
        pix_std(asic_idx, cap_idx) = std(10*log10(flat_pix));
	pix_mean(asic_idx, cap_idx) = 10*log10(mean(curr_flat_asic));
      endif
    endfor
  endfor
endfor

ff_filename = 'flatfield.raw';
ff_file = fopen(ff_filename, 'wb');

for cap_idx = 1:num_caps
  curr_frame = flat_raster(:,:,cap_idx)';
  fwrite(ff_file, curr_frame, "double", 0, "l");
endfor

fclose(ff_file)

# New code - write out the NaN'ified F-B file for inspection w imageJ
ff_filename = 'raw_flatfield.raw';
raw_ff_file = fopen(ff_filename, 'wb');

for cap_idx = 1:num_caps
  curr_frame = bg_sub_image(:,:,cap_idx)';
  fwrite(raw_ff_file, curr_frame, "double", 0, "l");
endfor

fclose(raw_ff_file)

#


figure(1)
subplot(1,1,1)
h = bar(pix_mean(:,1)-pix_mean(1,1))
title("ASIC Gain Compared to ASIC 1")
xlabel("ASIC Number")
ylabel("Gain (dB)")
print asic_gains.png

figure(2)
subplot(1,1,1)
plot(1:asic_count, pix_std(:,1), '-b*')
title("ASIC Flatness")
xlabel("Cap Number")
ylabel("Std Dev of Flatfield Gain (dB)")
print asic_flatness.png



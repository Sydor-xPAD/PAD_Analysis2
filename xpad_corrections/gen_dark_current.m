clear

cfg_filename = 'dark_current.ini';
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
  elseif strcmp(curr_name, "x_margin")
    x_margin = str2double(curr_val);
  elseif strcmp(curr_name, "y_margin")
    y_margin = str2double(curr_val);
  elseif strcmp(curr_name, "dark_image_filename")
    dark_image_filename = curr_val;
  elseif strcmp(curr_name, "bright_image_filename")
    bright_image_filename = curr_val;
  elseif strcmp(curr_name, "start_time")
    start_time = str2double(curr_val);
  elseif strcmp(curr_name, "end_time")
    end_time = str2double(curr_val);
  elseif strcmp(curr_name, "dark_mask")
    dark_mask_filename = curr_val;
  elseif strcmp(curr_name, "hot_mask")
    hot_mask_filename = curr_val;
  elseif strcmp(curr_name, "bpp")
    sensor_bpp = str2double(curr_val);
  elseif strcmp(curr_name, "asics_in_use")
    asics_in_use = str2num(curr_val);
  endif
endfor

num_skip_frames = num_caps * num_skip_images; # Total frames to skip

asic_x_count = image_width/asic_width;
asic_y_count = image_height/asic_height;
asic_count = asic_x_count * asic_y_count;

## Load in the whole stack
[raw_dark, num_frames] = read_xpad_image(dark_image_filename, sensor_bpp, offset, gap, image_width, image_height);

printf("Total dark frames: %i\n", num_frames);

if mod(num_frames, num_caps) != 0
  error("Error: Frame count is not a multiple of number of caps.");
endif

raw_dark = raw_dark(:,:, (num_skip_frames+1):num_frames);

dark_mean = mean(raw_dark,3);

clear raw_dark

## Load in the whole stack of bright images
[raw_bright, num_frames] = read_xpad_image(bright_image_filename, sensor_bpp, offset, gap, image_width, image_height);

printf("Total bright frames: %i\n", num_frames);

if mod(num_frames, num_caps) != 0
  error("Error: Frame count is not a multiple of number of caps.");
endif

raw_bright = raw_bright(:,:, (num_skip_frames+1):num_frames);

bright_mean = mean(raw_bright,3);

clear raw_bright

diff_stack = bright_mean - dark_mean;

## We now need to NaN out the bad pixels.  These are contained in two PGM files
## Change the filenames here to suit.
#bad_dark_pixels = imread(dark_mask_filename);
#bad_hot_pixels = imread(hot_mask_filename);
#disp('Loaded bad pixel maps')
#bad_pixels = bad_dark_pixels+bad_hot_pixels;
#bad_pixel_loc = find(bad_pixels != 0);

## Set all bad flat pixels to NaN
## Iterate over all caps
#for slice_idx = 1:(num_frames/2)
#  curr_slice = diff_stack(:,:,slice_idx);
#  curr_slice(bad_pixel_loc) = NaN;
#  diff_stack(:,:,slice_idx) = curr_slice;
#endfor

#diff_file = fopen("read_noise_diff.raw", "wb");
#fwrite(diff_file, reshape(diff_stack,1,[]), "float64");
#fclose(diff_file);


## Compute a standard deviation for each ASIC
raw_mean = zeros(asic_count, 1);
separate_mean = zeros(asic_count,1);
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

    curr_asic = diff_stack(row_lower:row_upper, col_lower:col_upper);
      
    raw_mean(asic_idx) = mean(reshape(curr_asic, 1, []));
  endfor
endfor

csv_file = fopen("dark_current.csv", "w");
elapsed_time = end_time - start_time;

printf("Dark Current (ADU/s):\n")
## Fancy Printing w00t!eleventy!!1!
printf("ASIC    Dark Current\n");
fprintf(csv_file, "Dark Current (ADU/s):\n");
fprintf(csv_file, "ASIC, Current\n");

for asic_idx=asics_in_use
  printf("%4i    ", asic_idx)
  fprintf(csv_file, "%i", asic_idx)
  printf("%-6.3f", raw_mean(asic_idx))
  fprintf(csv_file, ",%6.3f", raw_mean(asic_idx));
  printf("\n")
  fprintf(csv_file, "\n")
endfor

fclose(csv_file);

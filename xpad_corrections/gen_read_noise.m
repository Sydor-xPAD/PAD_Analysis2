clear

cfg_filename = 'read_noise.ini';
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


## Subtract the stacks
stack_one_idx = 1:(num_frames/2);
stack_two_idx = (num_frames/2+1):(num_frames);
diff_stack = raw_dark(:,:,stack_two_idx) - raw_dark(:,:,stack_one_idx);

## We now need to NaN out the bad pixels.  These are contained in two PGM files
## Change the filenames here to suit.
bad_dark_pixels = imread(dark_mask_filename);
bad_hot_pixels = imread(hot_mask_filename);
disp('Loaded bad pixel maps')
bad_pixels = bad_dark_pixels+bad_hot_pixels;
bad_pixel_loc = find(bad_pixels != 0);

## Set all bad flat pixels to NaN
## Iterate over all caps
for slice_idx = 1:(num_frames/2)
  curr_slice = diff_stack(:,:,slice_idx);
  curr_slice(bad_pixel_loc) = NaN;
  diff_stack(:,:,slice_idx) = curr_slice;
endfor

diff_file = fopen("read_noise_diff.raw", "wb");
fwrite(diff_file, reshape(diff_stack,1,[]), "float64");
fclose(diff_file);


             # Compute a standard deviation for each ASIC for each cap
raw_cap_noise = zeros(asic_count, num_caps);
separate_cap_noise = zeros(asic_count, num_caps);
asic_idx = 0;

printf("Frames Per Cap: %i\n", (num_frames/2/num_caps));

for cap_idx = 1:num_caps
  asic_idx = 0;
  cap_lower = cap_idx;
  cap_range = cap_lower:num_caps:(num_frames/2);
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

      if asic_idx == 7
        asic_7 = diff_stack(row_lower:row_upper, col_lower:col_upper, :);
      endif
      
      curr_asic = diff_stack(row_lower:row_upper, col_lower:col_upper, cap_range);
      
      raw_cap_noise(asic_idx, cap_idx) = calc_read_noise(curr_asic, 1);
      separate_cap_noise(asic_idx, cap_idx) = calc_read_noise(curr_asic, 0);
    endfor
  endfor
endfor

full_noise = mean(raw_cap_noise,2);


csv_file = fopen("read_noise.csv", "w");

printf("Total Noise:\n")
## Fancy Printing w00t!eleventy!!1!
printf("        Cap\n");
printf("ASIC    ");
fprintf(csv_file, "Total Noise:\n");
fprintf(csv_file, ",Cap\n");
fprintf(csv_file, "ASIC");
for cap_idx=1:num_caps
  printf("%-8i", cap_idx);
  fprintf(csv_file, ",%i", cap_idx);
endfor
printf("\n")
fprintf(csv_file, "\n")

for asic_idx=asics_in_use
  printf("%4i    ", asic_idx)
  fprintf(csv_file, "%i", asic_idx)
  for cap_idx=1:num_caps
    printf("%-6.3f  ", raw_cap_noise(asic_idx, cap_idx))
    fprintf(csv_file, ",%6.3f",raw_cap_noise(asic_idx, cap_idx));
  endfor
  printf("\n")
  fprintf(csv_file, "\n")
endfor

printf("\n")
fprintf(csv_file, "\n")

printf("Per-Frame Noise:\n")
printf("        Cap\n");
printf("ASIC    ");
fprintf(csv_file, "Per-Frame Noise:\n");
fprintf(csv_file, ",Cap\n");
fprintf(csv_file, "ASIC");
for cap_idx=1:num_caps
  printf("%-8i", cap_idx);
  fprintf(csv_file, ",%i", cap_idx);
endfor

printf("\n")
fprintf(csv_file, "\n")

for asic_idx=asics_in_use
  printf("%4i    ", asic_idx)
  fprintf(csv_file, "%i", asic_idx)
  for cap_idx=1:num_caps
    printf("%-6.3f  ", separate_cap_noise(asic_idx, cap_idx))
    fprintf(csv_file, ",%6.3f",separate_cap_noise(asic_idx, cap_idx));
  endfor
  printf("\n")
  fprintf(csv_file, "\n")
endfor

fclose(csv_file);

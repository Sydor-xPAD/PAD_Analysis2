clear

cfg_filename = 'flatfield_analysis.ini';
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
  elseif strcmp(curr_name, "dark_mask")
    dark_mask_filename = curr_val;
  elseif strcmp(curr_name, "hot_mask")
    hot_mask_filename = curr_val;
  elseif strcmp(curr_name, "bpp")
    sensor_bpp = str2double(curr_val);
  elseif strcmp(curr_name, "ff_map")
    ff_filename = curr_val;
  endif
endfor

# There are NUM_CAPS frames per image
num_skip_frames = num_caps * num_skip_images; #Total frames to skip

## Assemble parameters of the image geometry
asic_x_count = image_width/asic_width;
asic_y_count = image_height/asic_height;
asic_count = asic_x_count * asic_y_count;

## Put together the dark image mask
[dark_raw, num_dark_frames] = read_xpad_image(dark_image_filename, sensor_bpp, offset, gap, image_width, image_height);
printf("Total dark frames count: %i\n", num_dark_frames);
## Skip the bad images
if (num_skip_frames > 0)
  printf("Skipping %i images in dark frames.", num_skip_images);
  dark_raw = dark_raw(:,:,(num_skip_frames+1):num_dark_frames);
  num_dark_frames = num_dark_frames-num_skip_frames;
endif
printf("There are now %i frames in each dark cap.\n", num_dark_frames/num_caps);
dark_image = avg_caps(dark_raw, num_caps);
clear dark_raw

## Load the bright image, skipping frames as needed
[bright_raw, num_bright_frames] = read_xpad_image(bright_image_filename, sensor_bpp, offset, gap, image_width, image_height);
printf("Total bright frames count: %i\n", num_bright_frames);
if (num_skip_frames > 0)
  printf("Skipping %i images in bright frames.", num_skip_images);
  bright_raw = bright_raw(:,:,(num_skip_frames+1):num_bright_frames);
  num_bright_frames = num_bright_frames-num_skip_frames;
endif
printf("There are now %i frames in each bright cap.\n", num_bright_frames/num_caps);

## Now background subtract each frame in the bright image
bg_sub_img = zeros(size(bright_raw));
for frame_idx=1:num_bright_frames
  bg_sub_image(:,:,frame_idx) = bright_raw(:,:,frame_idx) - dark_image(:,:,mod(frame_idx,num_caps)+1);
endfor
clear bright_raw;               # No longer need the raw image

## Apply the bad-pixel masks
bad_dark_pixels = imread(dark_mask_filename);
bad_hot_pixels = imread(hot_mask_filename);
## -=-= XXX Makes no accounting for overflow of the sum, so the masks should only have values of 1
bad_pixels = bad_dark_pixels+bad_hot_pixels; #Combine the images
bad_pixel_loc = find(bad_pixels != 0);

## Set all the bad pixels to NaN
printf("Masking bad pixels.\n");
for frame_idx=1:num_bright_frames
  curr_frame = bg_sub_image(:,:,frame_idx);
  curr_frame(bad_pixel_loc) = NaN;
  bg_sub_image(:,:,frame_idx) = curr_frame;
endfor

## Load the flatfield map
ff_file = fopen(ff_filename, "rb");
flat_map = zeros(image_height, image_width, num_caps);
for cap_idx=1:num_caps
  curr_line = fread(ff_file, [image_width image_height], "double", "l");
  curr_line = curr_line';
  flat_map(:,:,cap_idx) = curr_line;
endfor

asic_avg_before = zeros(num_caps, asic_count);
asic_std_before = zeros(num_caps, asic_count);
max_pairs = floor(num_bright_frames/2);
pair_array = gen_pairs_array(max_pairs);
## Time for the before numbers
for cap_idx=1:num_caps
  for asic_idx=1:asic_count
    asic_row_idx = floor((asic_idx-1)/asic_x_count);
    asic_col_idx = mod((asic_idx-1), asic_x_count);

    ## Get the stack for the ASIC and cap
    asic_stack = bg_sub_image((asic_row_idx*asic_height+1):((asic_row_idx+1)*asic_height),(asic_col_idx*asic_width+1):((asic_col_idx+1)*asic_width),cap_idx:num_caps:num_bright_frames);
    ff_asic = flat_map((asic_row_idx*asic_height+1):((asic_row_idx+1)*asic_height),(asic_col_idx*asic_width+1):((asic_col_idx+1)*asic_width), cap_idx);
    
    pair_std = asbl_paired_img(asic_stack, pair_array, @std);
    pair_mean = asbl_paired_img(asic_stack, pair_array, @mean);

    x_reg = [(pair_array')*0+1 1./sqrt(pair_array')];
    coeff_reg = (x_reg'*x_reg)^-1*x_reg'*pair_std';
    y_reg = coeff_reg(1)+coeff_reg(2)./sqrt(pair_array);
    fixed_noise_x = [pair_array(1) pair_array(size(pair_array)(2))];
    fixed_noise_y = coeff_reg(1)*[1 1];

    figure(1)
    plot(pair_array, pair_std, "r-*;Measured Noise;", pair_array, pair_mean, 'b-^;Signal Mean;', pair_array, y_reg, 'g-s;Projected Noise;', fixed_noise_x, fixed_noise_y, "v-v;Calculated Fixed Noise;")
    chart_name = sprintf("noise_figure_%02i.png", asic_idx);
    print(chart_name);

    noise_stack = 10*log10(asic_stack/pair_mean(1));
    new_std = asbl_paired_img(noise_stack, pair_array, @std);
    figure(2)
    plot(pair_array, new_std, "r-*")
    chart_name = sprintf("noise_db_%02i.png", asic_idx);
    print(chart_name);

    ## Now apply the masks and get new figures
    flattened_asic = asic_stack;
    for frame_idx=1:num_bright_frames
      flattened_asic(:,:,frame_idx) = flattened_asic(:,:,frame_idx).*ff_asic;
    endfor
    flat_mean = asbl_paired_img(flattened_asic, pair_array, @mean);
    flattened_noise = 10*log10(flattened_asic/flat_mean(1));
    flat_std = asbl_paired_img(flattened_noise, pair_array, @std);
    figure(3)
    plot(pair_array, flat_std, "r-*");
    chart_name = sprintf("noise_flattened_%02i.png", asic_idx);
    print(chart_name);
    figure(4)
    plot(pair_array, new_std, "r-*;Before FF;", pair_array, flat_std, "b-s;After FF;");
    chart_name = sprintf("noise_combined_%02i.png", asic_idx);
    print(chart_name);
  endfor
endfor

                               
    
    

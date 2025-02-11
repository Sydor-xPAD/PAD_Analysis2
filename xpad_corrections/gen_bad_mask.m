clear -x filter_edge

cfg_filename = 'bad_pixel_mask.ini';
cfg_file = fopen(cfg_filename);
[cfg_list, file_status] = get_config_line(cfg_file);
fclose(cfg_file);

asic_width = 0;
asic_height = 0;
img_width = 0;
img_height = 0;
num_caps = 0
num_skip_images = 1
bad_asics = 1
hot_z_thresh = []
dark_z_thresh = []
prelim_bad_filename = ""
dark_image_filename = ""
bright_image_filename = ""
readnoise_image_filename = ""

for cfg_idx = 1:size(cfg_list)(1)
  curr_name = strtrim(cfg_list{cfg_idx, 1}{1,1});
  curr_val = strtrim(cfg_list{cfg_idx, 2}{1,1});

  if strcmp(curr_name, "asic_width")
    asic_width = str2double(curr_val);
  elseif strcmp(curr_name, "asic_height")
    asic_height = str2double(curr_val);
  elseif strcmp(curr_name, "img_width")
    img_width = str2double(curr_val);
  elseif strcmp(curr_name, "img_height")
    img_height = str2double(curr_val);
  elseif strcmp(curr_name, "num_caps")
    num_caps = str2double(curr_val)
  elseif strcmp(curr_name, "file_offset")
    offset = str2double(curr_val);
  elseif strcmp(curr_name, "file_gap")
    gap = str2double(curr_val);
  elseif strcmp(curr_name, "num_skip_images")
    num_skip_images = str2double(curr_val);
  elseif strcmp(curr_name, "bad_asics")
    bad_asics = str2num(curr_val);
  elseif strcmp(curr_name, "hot_iqr_thresh")
    hot_z_thresh = str2num(curr_val); # Actually a z-score later converted
  elseif strcmp(curr_name, "dark_iqr_thresh")
    dark_z_thresh = str2num(curr_val); # Actually a z-score later converted
  elseif strcmp(curr_name, "prelim_bad_filename")
    prelim_bad_filename = curr_val;
  elseif strcmp(curr_name, "dark_image_filename")
    dark_image_filename = curr_val;
  elseif strcmp(curr_name, "bright_image_filename")
    bright_image_filename = curr_val;
  elseif strcmp(curr_name, "read_noise_filename")
    readnoise_image_filename = curr_val;
  elseif strcmp(curr_name, "bpp")
    sensor_bpp = str2double(curr_val);
  endif
endfor


num_skip_frames = num_skip_images * num_caps;


## Compute the actual IQR-thresholds from the z-score thresholds
hot_iqr_thresh = (hot_z_thresh-0.67)/1.34;
dark_iqr_thresh = (dark_z_thresh-0.67)/1.34;

## Load in the preliminary bad pixels
prelim_bad_mask = imread(prelim_bad_filename);

## Now optionally filter out the edge pixels
if exist("filter_edge")
  if filter_edge != 0
    prelim_bad_mask(1:asic_height:img_height,:) = 1;
    prelim_bad_mask(asic_height:asic_height:img_height,:) = 1; # Filter out edge rows
    prelim_bad_mask(:,1:(asic_width*2):img_width) = 1;
    prelim_bad_mask(:,(asic_width*2):(asic_width*2):img_width) = 1; #Filter out submodule edge columns
  endif
endif

## Note where preliminary bad pixels are set
prelim_bad_mask = prelim_bad_mask != 0;

## Load in the the dark image
## Load in the whole stack...
[raw_dark, num_frames] = read_xpad_image(dark_image_filename, sensor_bpp, offset, gap, img_width, img_height);
## ...and process
[dark_img, num_frames] = clip_avg_stack(raw_dark, num_skip_frames, num_caps);
clear raw_dark

## Load in the hot image
## Load in the whole stack...
[raw_bright, num_frames] = read_xpad_image(bright_image_filename, sensor_bpp, offset, gap, img_width, img_height);
## ...and process
[bright_img, num_frames] = clip_avg_stack(raw_bright, num_skip_frames, num_caps);
clear raw_bright


## NaN out all bad pixels identified in pixel map
for cap_idx = 1:num_caps
  curr_slice = dark_image(:,:,cap_idx);
  curr_slice(find(prelim_bad_mask)) = NaN;
  dark_image(:,:,cap_idx) = curr_slice;
  curr_slice = bright_image(:,:,cap_idx);
  curr_slice(find(prelim_bad_mask)) = NaN;
  bright_image(:,:,cap_idx) = curr_slice;
endfor

## Now NaN out the bad asics
dark_image = apply_bad_asic(bad_asics, asic_height, asic_width, dark_image);
bright_image = apply_bad_asic(bad_asics, asic_height, asic_width, bright_image);

## Kludge for single caps
if num_caps == 1
  temp_image = zeros([size(dark_image) 2]);
  temp_image(:,:,1) = dark_image;
  temp_image(:,:,2) = dark_image;
  dark_image = temp_image;
endif

## Diff the images
diff_image = bright_image - dark_image;

size(dark_image)
## Threshold out the hot pixels
for curr_thresh=hot_iqr_thresh
  [hot_img, pix_thresh] = thresh_image(

## The threshold is the third argument in thresh_image(), below.
hot_filt = [];
total_bad = [];
masked_total_bad = [];
hot_bad = [];
cold_bad = [];
for curr_thresh=hot_iqr_thresh
  [hot_img, pix_thresh] = thresh_image(diff_image, 0, curr_thresh, asic_width, asic_height);
  hot_filt = [hot_filt pix_thresh];

  hot_total = sum(hot_img, 3);
  out_name = sprintf("hot_iqr_%.4f.pgm", 1.34*curr_thresh+0.67); #Switch to Z
  pgm_write(hot_total, out_name);
  out_name = sprintf("hot_iqr_%.4f_stack.pgm", 1.34*curr_thresh+0.67);
  pgm_write_stack(hot_img, out_name, num_caps);
  hot_bad = [hot_bad sum(reshape(isnan(hot_total),1,[]))];
endfor

## Now do similar to find the dark pixels

## Threshold out the hot pixels
## The threshold is the third argument in thresh_image(), below.
cold_filt = [];
for curr_thresh=dark_iqr_thresh
  [cold_img, curr_filt] = thresh_image(diff_image, 1, curr_thresh, asic_width, asic_height);
  cold_filt = [cold_filt curr_filt];

  cold_total = sum(cold_img, 3);
  out_name = sprintf("dark_iqr_%.4f.pgm", 1.34*curr_thresh+0.67);
  pgm_write(cold_total, out_name);
  out_name = sprintf("dark_iqr_%.4f_stack.pgm", 1.34*curr_thresh+0.67);
  pgm_write_stack(cold_img, out_name, num_caps);
  cold_bad = [cold_bad sum(reshape(isnan(cold_total),1,[]))];
endfor

## With the bad pixels calculated, we can collapse them to single layers for writing out
## This works by adding NaNs so that a NaN in any cap propagates to the total
hot_total = sum(hot_img, 3);
cold_total = sum(cold_img, 3);

## We can now write the images out to PGM files
## The pgm_write function is needed to convert NaNs and format the output properly
pgm_write(cold_total, "dark_pixels.pgm");
pgm_write(hot_total, "hot_pixels.pgm");

pgm_write_stack(hot_img, "hot_pixels.pgm", num_caps);
pgm_write_stack(cold_img, "dark_pixels.pgm", num_caps);

hot_bad
cold_bad

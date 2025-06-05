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
    num_caps = str2double(curr_val);
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
  elseif strcmp(curr_name, "bpp")
    sensor_bpp = str2double(curr_val);
  endif
endfor


num_skip_frames = num_skip_images * num_caps;

## Compute the actual IQR-thresholds from the z-score thresholds
hot_iqr_thresh = (hot_z_thresh-0.67)/1.34;
dark_iqr_thresh = (dark_z_thresh-0.67)/1.34

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

dark_image = zeros(img_height, img_width, num_caps);
bright_image = zeros(img_height, img_width, num_caps);

# Load in the the dark image and threshold
## Load in the whole stack
[raw_dark, num_frames] = read_xpad_image(dark_image_filename, sensor_bpp, offset, gap, 512, 512);

## Skip the first NUM_SKIP_IMAGE background images
## Remember there are NUM_CAPS frames per image
raw_dark = raw_dark(:,:,(num_skip_frames+1):num_frames);
num_frames = num_frames-num_skip_frames;

## Then average over each cap
for cap_idx = 1:num_caps
  dark_image(:,:,cap_idx) = mean(raw_dark(:,:,cap_idx:num_caps:num_frames),3);
endfor

clear raw_dark

## NaN out all bad pixels identified in pixel map
for cap_idx = 1:num_caps
  curr_slice = dark_image(:,:,cap_idx);
  curr_slice(find(prelim_bad_mask)) = NaN;
  dark_image(:,:,cap_idx) = curr_slice;
endfor

## Now NaN out the bad asics
dark_image = apply_bad_asic(bad_asics, asic_height, asic_width, dark_image);

## Kludge for single caps
if num_caps == 1
  temp_image = zeros([size(dark_image) 2]);
  temp_image(:,:,1) = dark_image;
  temp_image(:,:,2) = dark_image;
  dark_image = temp_image;
endif

size(dark_image)
## Threshold out the hot pixels
## The threshold is the third argument in thresh_image(), below.
hot_filt = [];
for curr_thresh=hot_iqr_thresh
  [hot_img, pix_thresh] = thresh_image(dark_image, 0, curr_thresh, asic_width, asic_height);
  hot_filt = [hot_filt pix_thresh];

  hot_total = sum(hot_img, 3);
  out_name = sprintf("hot_iqr_%.4f.pgm", 1.34*curr_thresh+0.67); #Switch to Z
  pgm_write(hot_total, out_name);
endfor

## Now do similar to find the dark pixels

## Load in the the dark image and threshold

## Load in the whole stack
[raw_bright, num_frames] = read_xpad_image(bright_image_filename, sensor_bpp, offset, gap, 512, 512);

## Skip the first NUM_SKIP_IMAGE flatfiled images
## Remember there are NUM_CAPS frames per image
raw_bright = raw_bright(:,:,(num_skip_frames+1):num_frames);
num_frames = num_frames-num_skip_frames;

## Then average over each cap
for cap_idx = 1:num_caps
  bright_image(:,:,cap_idx) = mean(raw_bright(:,:,cap_idx:num_caps:num_frames),3);
endfor

clear raw_bright

## NaN out all bad pixels identified in pixel map
for cap_idx = 1:num_caps
  curr_slice = bright_image(:,:,cap_idx);
  curr_slice(find(prelim_bad_mask)) = NaN;
  bright_image(:,:,cap_idx) = curr_slice;
endfor

## Now NaN out the bad asics
bright_image = apply_bad_asic(bad_asics, asic_height, asic_width, bright_image);

## Kludge for 1 cap
if num_caps == 1
  temp_image = zeros([size(bright_image) 2]);
  temp_image(:,:,1) = bright_image;
  temp_image(:,:,2) = bright_image;
  bright_image = temp_image;
endif

## Threshold out the hot pixels
## The threshold is the third argument in thresh_image(), below.
cold_filt = [];
for curr_thresh=dark_iqr_thresh
  [cold_img, curr_filt] = thresh_image(bright_image, 1, curr_thresh, asic_width, asic_height);
  cold_filt = [cold_filt curr_filt];

  cold_total = sum(cold_img, 3);
  out_name = sprintf("dark_iqr_%.4f.pgm", 1.34*curr_thresh+0.67);
  pgm_write(cold_total, out_name);
endfor

## With the bad pixels calculated, we can collapse them to single layers for writing out
## This works by adding NaNs so that a NaN in any cap propagates to the total
hot_total = sum(hot_img, 3);
cold_total = sum(cold_img, 3);

## We can now write the images out to PGM files
## The pgm_write function is needed to convert NaNs and format the output properly
pgm_write(cold_total, "dark_pixels.pgm");
pgm_write(hot_total, "hot_pixels.pgm");

clear

cfg_filename = 'debonce_col.ini';
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
  elseif strcmp(curr_name, "bg_image_filename")
    bg_image_filename = curr_val;
  elseif strcmp(curr_name, "dark_image_filename")
    dark_image_filename = curr_val;
  elseif strcmp(curr_name, "bright_image_glob")
    bright_image_glob = curr_val;
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

[raw_bg, num_frames] = read_xpad_image(bg_image_filename, sensor_bpp, offset, gap, image_width, image_height);
raw_bg = mean(raw_bg(:,:,3:num_frames), 3);

## Load in the whole stack
[raw_light, num_frames] = read_xpad_image(dark_image_filename, sensor_bpp, offset, gap, image_width, image_height);
raw_light = double(raw_light);
printf("Total light frames: %i\n", num_frames);

if mod(num_frames, num_caps) != 0
  error("Error: Frame count is not a multiple of number of caps.");
endif

## Compute the background image
raw_light = raw_light(:,:,3:num_frames);
num_frames = num_frames - 2;

#bg_light = raw_light(:,:,1:(num_frames/2))-raw_light(:,:,(num_frames/2+1):num_frames);

#num_frames = num_frames/2;

## FIXME DEBUGGING REMOVETHIS
#bg_light = raw_light(:,:,2:num_frames) - raw_light(:,:,1);
bg_light = raw_light - raw_bg;
bg_light = bg_light(129:256,1:256,:);

bg_mean = mean(reshape(bg_light(10:118,90:120,:), 109*31, []), 1);

for frame_idx = 1:(num_frames/num_caps)
  db_light(:,:,frame_idx) = bg_light(:,:,frame_idx) - bg_mean(frame_idx);
endfor

chunk = db_light(60:110,10:60,:);
strip = reshape(chunk, 51*51, []);
strip_raw = reshape(bg_light(60:110,10:60,:), 51*51, []);
std(strip)
std(strip_raw)

subplot(2,1,1)
plot(mean(strip,1)-mean(strip,1)(1))
subplot(2,1,2)
plot(mean(strip_raw,1)-mean(strip_raw,1)(1))

db_file = fopen("db_light.raw", "wb");
rb_file = fopen("rb_light.raw", "wb");
for frame_idx=1:num_frames
  curr_frame = db_light(:,:,frame_idx)';
  fwrite(db_file, curr_frame, "double", 0, "l");
  curr_frame = bg_light(:,:,frame_idx)';
  fwrite(rb_file, curr_frame, "double", 0, "l");
endfor

fclose(db_file);
fclose(rb_file);

stats_file = fopen("db_stats.csv", "w");
mean_array = [mean(strip_raw,1)'-mean(strip_raw,1)(1)  mean(strip,1)'-mean(strip,1)(1)];
mean_array = [mean(strip_raw,1)'  mean(strip,1)']';
fprintf(stats_file, "%f,%f\n", mean_array);
fclose(stats_file)

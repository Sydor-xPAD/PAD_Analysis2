clear -x filter_edge

cfg_filename = 'flatfield_map.ini';
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
  elseif strcmp(curr_name, "diff_image_filename")
    diff_image_filename = curr_val;
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

## Assemble a mask of chip edge pixels
edge_mask = zeros(image_height, image_width);
edge_mask(1:asic_height:image_height,:) = 1;
edge_mask(asic_height:asic_height:image_height,:) = 1;
edge_mask(:, 1:(asic_width*2):image_width) = 1;
edge_mask(:, (asic_width*2):(asic_width*2):image_width) = 1;
edge_pixels = find(edge_mask != 0);

## Load in the averaged dark stack

bg_sub_file = fopen(diff_image_filename, "rb");
bg_sub_image = zeros(image_height, image_width, num_caps);

for cap_idx=1:num_caps
  [curr_frame, count_read] = fread(bg_sub_file, [image_width, image_height], "double", 0, "l");
  bg_sub_image(:,:,cap_idx) = curr_frame';
endfor

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
pix_fq = zeros(asic_count, num_caps);
pix_tq = zeros(asic_count, num_caps); #First and third quartiles
pix_rawmean = zeros(asic_count, num_caps);
pix_rawmed = zeros(asic_count, num_caps);


flat_mean = zeros(asic_count, num_caps);
flat_fq = zeros(asic_count, num_caps);
flat_tq = zeros(asic_count, num_caps);
flat_med = zeros(asic_count, num_caps);

for cap_idx = 1:num_caps
  curr_frame = bg_sub_image(:,:,cap_idx);
  ## Second parameter below is the threshold of gain deemed too low.
  flattened_pixels = calc_flat_asic(curr_frame, gain_thresh);
  if exist("filter_edge") != 0
    if filter_edge != 0
      flattened_pixels(edge_pixels) = flattened_pixels(edge_pixels)./flattened_pixels(edge_pixels); # Set non-NaN edge pixels to unity; NaN->NaN, 0 removed by gain_thresh, x/x = 1
    endif
  endif
  
  flat_raster(:,:,cap_idx) = flattened_pixels;
                                                                           
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
      curr_asic_line = curr_asic_pix(1:numel(curr_asic_pix));
      curr_asic_line = curr_asic_line(find(isfinite(curr_asic_line)));
      curr_flat_asic = flat_raster(row_lower:row_upper,col_lower:col_upper,cap_idx);
      curr_flat_asic = reshape(curr_flat_asic, 1, []);
      curr_flat_asic = curr_flat_asic(find(isfinite(curr_flat_asic)));
      flat_pix = reshape(calc_flat_asic(curr_asic_pix, gain_thresh),1, []);
      flat_pix = flat_pix(find(isfinite(flat_pix)));
      if isempty(flat_pix)
        pix_std(asic_idx, cap_idx) = NaN;
        pix_mean(asic_idx, cap_idx) = NaN;          # This should be an invalid value
        pix_rawmean(asic_idx, cap_idx) = NaN;
        flat_mean(asic_idx, cap_idx) = NaN;
        flat_fq(asic_idx, cap_idx) = NaN;
        flat_tq(asic_idx, cap_idx) = NaN;
        pix_rawmed(asic_idx, cap_idx) = NaN;
        flat_med(asic_idx, cap_idx) = NaN;
      else
        pix_std(asic_idx, cap_idx) = std(10*log10(flat_pix));
	pix_mean(asic_idx, cap_idx) = 10*log10(mean(curr_flat_asic));
        quartiles = prctile(curr_asic_line, [0.25 0.75 0.5]);
        pix_fq(asic_idx, cap_idx) = quartiles(1);
        pix_tq(asic_idx, cap_idx) = quartiles(2);
        pix_rawmed(asic_idx, cap_idx) = quartiles(3);
        pix_rawmean(asic_idx, cap_idx) = mean(curr_asic_line);
        flat_mean(asic_idx, cap_idx) = mean(curr_flat_asic);
        quartiles = prctile(curr_flat_asic, [0.25 0.75 0.5 ]);
        flat_fq(asic_idx, cap_idx) = quartiles(1);
        flat_tq(asic_idx, cap_idx) = quartiles(2);
        flat_med(asic_idx, cap_idx) = quartiles(3);
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

figure(1)
subplot(1,1,1)
h = bar(0:(asic_count-1),1*(10.^(0.1*(pix_mean(:,1)-pix_mean(1,1)))))
title("ASIC Gain Compared to ASIC 1")
axis([0 35])
xlabel("ASIC Number")
ylabel("Gain (%)")
set(h(1), "basevalue", 1.0);
print asic_gains.png

figure(2)
subplot(1,1,1)
plot(1:asic_count, pix_std(:,1), '-b*')
title("ASIC Flatness")
xlabel("Cap Number")
ylabel("Std Dev of Flatfield Gain (dB)")
print asic_flatness.png

figure(3)
subplot(1,1,1)
errorbar(1:asic_count, pix_rawmean(:,1), pix_rawmean(:,1)-pix_fq(:,1), pix_tq(:,1)-pix_rawmean(:,1))
hold on
plot(1:asic_count, pix_rawmed(:,1), 'r-')
hold off

figure(4)
subplot(1,1,1)
errorbar(1:asic_count, flat_mean(:,1), flat_mean(:,1)-flat_fq(:,1), flat_tq(:,1)-flat_mean(:,1))
hold on
plot(1:asic_count, flat_med(:,1), 'r-')
hold off

# YF test
#imshow(curr_frame)

for cap_idx=1:8
  
  figure(10+cap_idx)
  subplot(1,1,1)
  h = bar(0:(asic_count-1),1*(10.^(0.1*(pix_mean(:,cap_idx)-pix_mean(1,1)))))
  title_str = sprintf("Cap %i ASIC Gain Compared to ASIC 0, Cap 0", cap_idx-1);
  title(title_str)
  axis([-1 35])
  xlabel("ASIC Number")
  ylabel("Gain (%)")
  set(h(1), "basevalue", 1.0);
  out_name = sprintf("asic_gains_cap%i.png", cap_idx-1);
  print(out_name)

endfor

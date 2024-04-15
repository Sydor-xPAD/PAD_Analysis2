clear

cfg_filename = 'linearity.ini';
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

## Load in the whole stack
[raw_dark, num_frames] = read_xpad_image(dark_image_filename, sensor_bpp, offset, gap, image_width, image_height);
raw_dark_base = raw_dark;
raw_dark = double(raw_dark);
printf("Total dark frames: %i\n", num_frames);

if mod(num_frames, num_caps) != 0
  error("Error: Frame count is not a multiple of number of caps.");
endif

## Compute the background image
raw_dark = mean(raw_dark,3);

## FIXME DEBUGGING REMOVETHIS
#raw_dark = raw_dark - raw_dark;

## We now need to NaN out the bad pixels.  These are contained in two PGM files
## Change the filenames here to suit.
bad_dark_pixels = imread(dark_mask_filename);
bad_hot_pixels = imread(hot_mask_filename);
disp('Loaded bad pixel maps')
bad_pixels = bad_dark_pixels+bad_hot_pixels;
bad_pixel_loc = find(bad_pixels != 0);


## Get the foreground files
bright_file_list = glob(bright_image_glob)
num_fg = size(bright_file_list)(1);

sigmasq_vals = zeros(asic_count, num_fg);
mu_vals = zeros(asic_count, num_fg);

for fg_idx=1:num_fg
  bright_filename = bright_file_list{fg_idx}
  [raw_bright, num_frames] = read_xpad_image(bright_filename, sensor_bpp, offset, gap, 512, 512);

  raw_bright = double(raw_bright);
  printf("Loaded %i foreground frames.\n", num_frames);

  ## Set all bad flat pixels to NaN
  ## Iterate over all caps
  for slice_idx = 1:(num_frames)
    curr_slice = raw_bright(:,:,slice_idx);
                                #-=-= NOTE Also squeeze in BG sub
    curr_slice = curr_slice - raw_dark;
    curr_slice(bad_pixel_loc) = NaN;
    raw_bright(:,:,slice_idx) = curr_slice;
  endfor

  imagesc(raw_bright)
  
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

      curr_asic = raw_bright(row_lower:row_upper, col_lower:col_upper, :);
      [curr_sigmasq, curr_mu] = calc_linearity_vals(curr_asic);
      sigmasq_vals(asic_idx, fg_idx) = curr_sigmasq;
      mu_vals(asic_idx, fg_idx) = curr_mu;
    endfor
  endfor
endfor

csv_file = fopen("linearity.csv", "w");

for curr_asic=asics_in_use
  figure(1)
  subplot(1,1,1)
  ## sort the data in rows
  [sort_mu, sort_idx] = sort(mu_vals(curr_asic,:));
  sort_var = sigmasq_vals(curr_asic,:)(sort_idx);
  
  title_string = sprintf("ASIC %i", curr_asic);
  plot(sort_mu, sort_var, '-b*')
  title(title_string)
  xlabel('Frame Mean (ADU)')
  ylabel('Frame Variance (ADU^2)')
  filename_string = sprintf("linearity_asic%02i.png", curr_asic);
  print(filename_string)

  ## Now print a nice table
  printf("ASIC %i\n", curr_asic)
  printf("%-16s%-16s\n", "Mean", "Variance")

  fprintf(csv_file, "ASIC %i\n", curr_asic);
  fprintf(csv_file, "Mean,Variance\n")
  
  for mu_idx=1:max(size(sort_mu))
    printf("%-+12.3e    %-+12.3e\n", sort_mu(mu_idx), sort_var(mu_idx));
    fprintf(csv_file, "%12.3e,%12.3e\n", sort_mu(mu_idx), sort_var(mu_idx));
  endfor
  printf("\n")
  fprintf(csv_file, "\n");
endfor

fclose(csv_file)

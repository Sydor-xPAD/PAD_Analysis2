clear

cfg_filename = 'sensor_char.ini';
cfg_file = fopen(cfg_filename);
[cfg_list, file_status] = get_config_line(cfg_file);
fclose(cfg_file);

do_dark_analysis = false;
do_dark_current = false;
do_read_noise = false;
do_flatness = false;

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
  elseif strcmp(curr_name, "short_dark_image_filename")
    short_dark_image_filename = curr_val;
  elseif strcmp(curr_name, "long_dark_image_filename")
    long_dark_image_filename = curr_val;
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
  elseif strcmp(curr_name, "max_frames")
    max_frames = str2double(curr_val);
  elseif strcmp(curr_name, "do_dark_analysis")
    do_dark_analysis = str2num(curr_val);
  elseif strcmp(curr_name, "do_dark_current")
    do_dark_current = str2num(curr_val);
  elseif strcmp(curr_name, "do_read_noise")
    do_read_noise = str2num(curr_val);
  elseif strcmp(curr_name, "do_flatness")
    do_flatness = str2num(curr_val);
  endif
endfor

num_skip_frames = num_skip_images * num_caps;
num_x_asics = image_width / asic_width;
num_y_asics = image_height / asic_height;
num_asics = num_x_asics * num_y_asics;

img_desc.asic_width = asic_width;
img_desc.asic_height = asic_height;
img_desc.img_width = image_width;
img_desc.img_height = image_height;
img_desc.num_x_asics = num_x_asics;
img_desc.num_y_asics = num_y_asics;
img_desc.num_asics = num_asics;
img_desc.x_margin = x_margin;
img_desc.y_margin = y_margin;

## First perform the dark analysis

if do_dark_analysis
  [raw_dark_stack, num_dark_frames] = read_xpad_image(short_dark_image_filename, sensor_bpp, offset, gap, image_width, image_height, max_frames);
  
  raw_dark_stack = raw_dark_stack(:,:,(num_skip_frames+1):num_dark_frames);
  num_dark_frames = num_dark_frames - num_skip_frames;
  # -=-= TODO IM Add in bad pixel calculation

  pedestal_level = zeros(num_asics, num_caps);
  pedestal_noise = zeros(num_asics, num_caps);
  full_pedestal_image = zeros(image_height, image_width,num_caps);
  
  for cap_idx=1:num_caps
    for asic_idx=1:num_asics
      base_name = sprintf("dark_analysis_c%i_asic%02i", cap_idx, asic_idx);
      curr_margin = calc_bounds(asic_idx-1, img_desc);
      curr_stack = raw_dark_stack(curr_margin.y_base_min:curr_margin.y_base_max, curr_margin.x_base_min:curr_margin.x_base_max, cap_idx:num_caps:num_dark_frames);
      [pedestal_img, p_mean, p_std] = fcn_dark_analysis(base_name, curr_stack);
      pedestal_level(asic_idx, cap_idx) = p_mean;
      pedestal_noise(asic_idx, cap_idx) = p_std;
      full_pedestal_image(curr_margin.y_base_min:curr_margin.y_base_max, curr_margin.x_base_min:curr_margin.x_base_max, cap_idx) = pedestal_img;
    endfor
    plot(1:num_asics, pedestal_level(:,cap_idx), 'b-');
    title(sprintf("Reset Pedestal Brightness - Cap %i", cap_idx));
    ylabel("ADU")
    xlabel("ASIC #")
    out_name = sprintf("dark_pedestal_mean_cap%i.png", cap_idx);
    print(out_name);
    plot(1:num_asics, pedestal_noise(:,cap_idx), 'b-');
    title(sprintf("Reset Pedestal Noise - Cap %i", cap_idx));
    ylabel("ADU")
    xlabel("ASIC #")
    out_name = sprintf("dark_pedestal_noise_cap%i.png", cap_idx);
    print(out_name);
  endfor

  img_filename = "dark_pedestal.raw";
  img_file = fopen(img_filename, "wb");
  for cap_idx=1:num_caps
    curr_slice = full_pedestal_image(:,:,cap_idx);
    fwrite(img_file, curr_slice'(1:numel(curr_slice)), "double", 0, "l");
  endfor
  fclose(img_file);
  clear raw_dark_stack
endif

if do_read_noise
  [raw_dark_stack, num_dark_frames] = read_xpad_image(short_dark_image_filename, sensor_bpp, offset, gap, image_width, image_height, max_frames);
  
  raw_dark_stack = raw_dark_stack(:,:,(num_skip_frames+1):num_dark_frames);
  num_dark_frames = num_dark_frames - num_skip_frames;
  ## -=-= TODO IM Add in bad pixel calculation

  ## Create the pairs of stacks
  sub_dark_stack = raw_dark_stack(:,:,1:(num_dark_frames/2))-raw_dark_stack(:,:,(num_dark_frames/2+1):num_dark_frames);

  total_read_noise = zeros(num_asics, num_caps); #Read noise including bounce
  seprate_read_noise = zeros(num_asics, num_caps);  #Read noise exlcuding bounce
  
  for cap_idx=1:num_caps
    for asic_idx=1:num_asics
      base_filename = sprintf("noise_analysis_c%i_asic%02i", cap_idx, asic_idx);
      base_title = sprintf("Noise Analysis - Cap %i ASIC %02i", cap_idx, asic_idx);
      curr_margin = calc_bounds(asic_idx-1, img_desc);
      curr_stack = sub_dark_stack(curr_margin.y_margin_min:curr_margin.y_margin_max, curr_margin.x_margin_min:curr_margin.x_margin_max, cap_idx:num_caps:(num_dark_frames/2));

      total_read_noise(asic_idx, cap_idx) = calc_read_noise(curr_stack, 1);
      separate_read_noise(asic_idx, cap_idx) = calc_read_noise(curr_stack, 0);
    endfor
  endfor


  csv_filename{1} = "read_noise_bounce.csv";
  csv_filename{2} = "read_noise_nobounce.csv";

  for csv_idx=1:2
    if csv_idx==1
      noise_var = total_read_noise;
    else
      noise_var = separate_read_noise;
    endif
    
    csv_file = fopen(csv_filename{csv_idx}, "w");

    fprintf(csv_file, "#Noise\n");
    fprintf(csv_file, "#ASIC");
    for cap_idx=1:num_caps
      fprintf(csv_file, ",Cap %i", cap_idx);
    endfor
    fprintf(csv_file, "\n");

    for asic_idx=1:num_asics
      fprintf(csv_file, "%i", asic_idx);
      for cap_idx=1:num_caps
        fprintf(csv_file, ",%6.3f", noise_var(asic_idx, cap_idx));
      endfor
      fprintf(csv_file, "\n")
    endfor
    fclose(csv_file);
  endfor
  clear raw_dark_stack
  clear sub_dark_stack
endif

if do_flatness
  [raw_dark_stack, num_dark_frames] = read_xpad_image(short_dark_image_filename, sensor_bpp, offset, gap, image_width, image_height, max_frames);
  
  raw_dark_stack = raw_dark_stack(:,:,(num_skip_frames+1):num_dark_frames);
  num_dark_frames = num_dark_frames - num_skip_frames;
  ## -=-= TODO IM Add in bad pixel calculation

  dark_image = avg_caps(raw_dark_stack, num_caps);
  clear raw_dark_stack
    
  [raw_bright_stack, num_bright_frames] = read_xpad_image(bright_image_filename, sensor_bpp, offset, gap, image_width, image_height, max_frames);
  
  raw_bright_stack = raw_bright_stack(:,:,(num_skip_frames+1):num_bright_frames);
  num_bright_frames = num_bright_frames - num_skip_frames;

  bg_sub_image = zeros(size(raw_bright_stack));
  for frame_idx=1:num_bright_frames
    bg_sub_image(:,:,frame_idx) = raw_bright_stack(:,:,frame_idx) - dark_image(:,:,mod(frame_idx,num_caps)+1);
  endfor

  clear raw_bright_stack
  
  ## -=-= TODO IM Add in bad pixel calculation

  ## Load the flatfield map
  ff_file = fopen(ff_filename, "rb");
  flat_map = zeros(image_height, image_width, num_caps);
  for cap_idx=1:num_caps
    curr_line = fread(ff_file, [image_width image_height], "double", "l");
    curr_line = curr_line';
    flat_map(:,:,cap_idx) = curr_line;
  endfor
  fclose(ff_file);

  asic_mean_before = zeros(num_asics, num_caps);
  asic_std_before = zeros(num_asics, num_caps);
  max_pairs = floor((num_bright_frames/num_caps)/2);
  pair_array = gen_pairs_array(max_pairs);
  fixed_noise = zeros(num_asics, num_caps);
  flat_noise = zeros(num_asics, num_caps);

  ## Compute the numbers before applying the flatfield
  for cap_idx=1:num_caps
    for asic_idx=1:num_asics
      base_title = sprintf("Flat Image Cap %i ASIC %02i", cap_idx, asic_idx);
      base_name = sprintf("flat_img_c%i_asic%02i", cap_idx, asic_idx);
      coord_title = sprintf("Cap %i ASIC %02i", cap_idx, asic_idx);
      coord_name = sprintf("c%i_asic%02i", cap_idx, asic_idx);
      curr_margin = calc_bounds(asic_idx-1, img_desc);
      curr_stack = bg_sub_image(curr_margin.y_margin_min:curr_margin.y_margin_max, curr_margin.x_margin_min:curr_margin.x_margin_max, cap_idx:num_caps:num_bright_frames);
      ff_asic = flat_map(curr_margin.y_margin_min:curr_margin.y_margin_max, curr_margin.x_margin_min:curr_margin.x_margin_max, cap_idx);

      pair_std = asbl_paired_img(curr_stack, pair_array, @nanstd);
      pair_mean = asbl_paired_img(curr_stack, pair_array, @nanmean);

      [noise_coeff, pred_noise] = calc_noise_reg(pair_array, pair_std);
      fixed_noise_x = [pair_array(1) pair_array(numel(pair_array))];
      fixed_noise_y = noise_coeff(1)*[1 1];

      plot(pair_array, pair_std, "r*;Measured Noise;", pair_array, pred_noise, 'b-;Projected Noise;', fixed_noise_x, fixed_noise_y,"v-;Calculated Fixed Noise;");
      title(["Flat Image Measurements" coord_title]);
      xlabel("# Pairs")
      ylabel("Noise (ADU)")
      chart_name = ["noise_figure" coord_name ".png"];
      print(chart_name)

      noise_stack = 10*log10(curr_stack/pair_mean(1));
      new_std = asbl_paired_img(noise_stack, pair_array, @nanstd);
      new_std = 10.^(new_std/10)*100-100;
      plot(pair_array, new_std, 'r-*');
      title(["Gain Noise " coord_title]);
      xlabel("# Pairs")
      ylabel("Noise (%)")
      chart_name = ["noise_normalized" coord_name ".png"];
      print(chart_name)

      ## Now apply the flatfield
      flattened_asic = curr_stack;
      for frame_idx=1:(num_bright_frames/num_caps)
        flattened_asic(:,:,frame_idx) = flattened_asic(:,:,frame_idx).*ff_asic;
      endfor

      flat_mean = asbl_paired_img(flattened_asic, pair_array, @nanmean);
      flattened_noise = 10*log10(flattened_asic/flat_mean(1));
      flat_std = asbl_paired_img(flattened_noise, pair_array, @nanstd);
      flat_std = 100*10.^(flat_std/10)-100;

      plot(pair_array, new_std, "b-*;Before Flatfield;", pair_array, flat_std, "r-s;After Flatfield;")
      title(["Flat Noise Comparison " coord_title]);
      xlabel("# Pairs")
      ylabel("Flat Noise (%)")
      chart_name = ["noise_compare_" coord_name ".png"];
      print(chart_name);
    endfor
  endfor
endif

      

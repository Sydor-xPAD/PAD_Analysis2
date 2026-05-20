clear

input_filename = 'avg_image_8caps.raw';

input_file = fopen(input_filename, 'rb');

num_frames = 8;
asic_size = 128;
pixel_threshold = 0.005;

raster = zeros(512, 512, num_frames);
for frame_idx = 1:num_frames
  raster(:,:,frame_idx) = fread(input_file, [512 512], 'float', 'b')';
endfor

imagesc(raster(:,:,2))

fclose(input_file);
out_raster = raster;

% NaN out the bad ASICS
for asic_row_idx=0:3
  start_row = asic_row_idx*asic_size+1;
  end_row = (asic_row_idx+1)*asic_size;
  for asic_col_idx=0:3
    start_col = asic_col_idx*asic_size+1;
    end_col = (asic_col_idx+1)*asic_size;
    if ((asic_row_idx == 0) & (asic_col_idx == 1)) | ((asic_row_idx == 1) & (asic_col_idx == 0)) | ((asic_row_idx == 3) & (asic_col_idx==0))
      out_raster(start_row:end_row,start_col:end_col,:) = nan;
    endif
  endfor
endfor

thresh_raster = out_raster;

% Now NaN out the outliers
for frame_idx = 1:num_frames
  curr_frame = out_raster(:,:,frame_idx); # Get the frame
  curr_line = reshape(curr_frame, 1, []); # Make one-dimensional
  curr_line = curr_line(find(isfinite(curr_line)));
  curr_line = sort(curr_line);
  num_elems = max(size(curr_line));
  low_rank = floor(num_elems*pixel_threshold+1);
  high_rank = floor(num_elems*(1-pixel_threshold)+1);
  low_val = curr_line(low_rank);
  high_val = curr_line(high_rank);

  curr_frame(find(curr_frame >= high_val)) = NaN;
  curr_frame(find(curr_frame <= low_val)) = NaN;

  thresh_raster(:,:,frame_idx) = curr_frame;
endfor

imagesc(thresh_raster(:,:,2))
frame_mean = zeros(1, num_frames);
frame_std = zeros(1, num_frames);

for frame_idx = 1:num_frames
  curr_frame = thresh_raster(:,:,frame_idx);
  curr_array = reshape(curr_frame, 1, []);
  curr_array = curr_array(find(isfinite(curr_array)));
  curr_mean = mean(curr_array);
  curr_std = std(curr_array);
  frame_mean(frame_idx) = curr_mean;
  frame_std(frame_idx) = curr_std;
endfor

asic_mean = zeros(4, 4, num_frames);
asic_std = zeros(4, 4, num_frames);

mean_diff = zeros(4, 4, num_frames);
std_diff = zeros(4, 4, num_frames);

for frame_idx = 1:num_frames
  cap_mean = frame_mean(frame_idx);
  cap_std = frame_std(frame_idx);

  for asic_row_idx=0:3
    start_row = asic_row_idx*asic_size+1;
    end_row = (asic_row_idx+1)*asic_size;
    for asic_col_idx=0:3
      start_col = asic_col_idx*asic_size+1;
      end_col = (asic_col_idx+1)*asic_size;
      curr_asic_img = thresh_raster(start_row:end_row,start_col:end_col,frame_idx);
      curr_line = reshape(curr_asic_img, 1, []);
      curr_line = curr_line(find(isfinite(curr_line)));
      if (size(curr_line)(2) == 0) # All pixels NaN
        continue;
      endif

      curr_mean = mean(curr_line);
      curr_std = std(curr_line);

      asic_mean(asic_row_idx+1, asic_col_idx+1) = curr_mean;
      asic_std(asic_row_idx+1, asic_col_idx+1) = curr_std;

      mean_diff(asic_row_idx+1, asic_col_idx+1, frame_idx) = (curr_mean-cap_mean)/(0.5*(curr_mean+cap_mean));
      std_diff(asic_row_idx+1, asic_col_idx+1, frame_idx) = (curr_std-cap_std)/(0.5*(curr_mean+cap_mean));

    endfor
  endfor
endfor

abs_mean_diff = abs(mean_diff);
abs_std_diff = abs(std_diff);



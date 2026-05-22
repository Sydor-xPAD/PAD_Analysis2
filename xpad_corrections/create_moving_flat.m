clear
bright_filename = "set-Factory_Testing_11FEB2025C/moving_flat.raw";
dark_filename = "set-Factory_Testing_11FEB2025C/run-BG_20ms/frames/BG_20ms_00000001.raw"
out_flat_filename = "moving_flat_caps.raw"
num_caps = 8;
image_width = 1024;
image_height = 512;

[bright_image, num_frames] = read_xpad_image_short(bright_filename, 16, 256, 2048, image_width, image_height, 5601);

bright_avg_stack = zeros(image_height, image_width, num_caps);

for cap_idx=1:num_caps
  curr_cap = bright_image(:,:,cap_idx:num_caps:end);
  bright_avg_stack(:,:,cap_idx) = assemble_percentile_image(curr_cap, 0.75);
endfor
clear bright_image

[dark_image, num_frames] = read_xpad_image(dark_filename, 16, 256, 2048, image_width, image_height, 1001);

dark_avg_stack = clip_avg_stack(dark_image, 16, 8);

diff_stack = bright_avg_stack - dark_avg_stack;

out_file = fopen(out_flat_filename, "wb");
for cap_idx=1:num_caps
  fwrite(out_file, diff_stack(:,:,cap_idx)', "double", 0, "l");
endfor
fclose(out_file);


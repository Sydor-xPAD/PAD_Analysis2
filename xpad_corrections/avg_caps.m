function avg_array = avg_caps(base_image, num_caps)
  image_width = size(base_image)(2);
  image_height = size(base_image)(1);
  num_frames = size(base_image)(3);

  avg_array = zeros(image_height, image_width, num_caps);

  ## Average each cap
  for cap_idx = 1:num_caps
    avg_array(:,:,cap_idx) = mean(base_image(:,:,cap_idx:num_caps:num_frames),3);
  endfor

  return
endfunction


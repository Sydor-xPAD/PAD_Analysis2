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


#
#  This averages <N> of CAP1, then <N> of CAP2, etc...
#
function avg_array_not_interspersed = avg_caps(base_image, num_caps)
  image_width = size(base_image)(2);
  image_height = size(base_image)(1);
  num_frames = size(base_image)(3);  # ie 800 ish
  num_frames_per_cap = num_frames / num_caps  # ie: 100 ish

  avg_array = zeros(image_height, image_width, num_caps);

  ## Average each cap
  for cap_idx = 1:num_caps
    a = (cap_idx-1) * num_frames_per_cap + 1
    b = a + num_frames_per_cap
    avg_array(:,:,cap_idx) = mean(base_image(:,:,a:b),3);
  endfor

  return
endfunction

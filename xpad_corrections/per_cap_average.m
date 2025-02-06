function cap_avg_stack = per_cap_average(img, num_caps)
  cap_avg_stack = zeros(size(img)(1:2), num_caps);

  for cap_idx = 1:num_caps
    cap_avg_stack = mean(img(:,:,cap_idx:num_caps:end),3);
  endfor

  return
endfunction

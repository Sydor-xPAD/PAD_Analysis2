function [mod_img, pix_thresh_prop] = pixel_gain_filt_high(base_img, thresh)
  mod_img = base_img;
  curr_line = reshape(base_img, 1, []);
  curr_line = curr_line(find(isfinite(curr_line)));

  pix_thresh_prop = -5;         # Set a known-bad value in case we need to return
  if (size(curr_line)(2) == 0)  #All pixels NaN
    return                      # Nothing to filter out
  endif

  line_len = size(curr_line)(2);
  
  sort_line = sort(curr_line);

  thresh
  gain_mean = mean(sort_line)
  gain_median = median(sort_line);
  gain_std = std(sort_line);
  thresh_val = gain_median - thresh*gain_std;
  thresh_val = gain_median * thresh

  size(find(mod_img > thresh_val));
  pix_thresh_prop = max(size(find(mod_img > thresh_val)))/max(size(curr_line));
  mod_img(find(mod_img > thresh_val)) = NaN;
  
  printf("High pixels filtered: %f%%\n", pix_thresh_prop*100);
    
  return
endfunction


    

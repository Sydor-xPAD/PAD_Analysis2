function [mod_img, pix_thresh_prop] = pixel_iqr_filt(base_img, bLow, thresh)
  mod_img = base_img;
  pix_thresh_prop = -5;
  curr_line = reshape(base_img, 1, []);
  curr_line = curr_line(find(isfinite(curr_line)));

  if (size(curr_line)(2) == 0)  #All pixels NaN
    return                      # Nothing to filter out
  endif

  line_len = size(curr_line)(2);
  
  sort_line = sort(curr_line);
  
  img_iqr = iqr(sort_line); # Extract the IQR
  q1_idx = floor(line_len*0.25)+1;
  q3_idx = floor(line_len*0.75)+1;
  pix_thresh_prop = 0;
  
  if bLow != 0                  # Filter out low pixels
    thresh_val = sort_line(q1_idx) - thresh*img_iqr;  
    pix_thresh_prop = max(size(find(mod_img <= thresh_val)))/max(size(curr_line));
    mod_img(find(mod_img <= thresh_val)) = NaN;
  else                        # Filter out high pixels
    thresh_val = sort_line(q3_idx) + thresh*img_iqr;
    pix_thresh_prop = max(size(find(mod_img >= thresh_val)))/max(size(curr_line));
    mod_img(find(mod_img >= thresh_val)) = NaN;
  endif

  if bLow != 0 # Filtered out low pixels
    printf("Low pixels filtered: %f%%\n", pix_thresh_prop*100);
  else
    printf("High pixels filtered: %f%%\n", pix_thresh_prop*100);
  endif
  
  return
endfunction


    

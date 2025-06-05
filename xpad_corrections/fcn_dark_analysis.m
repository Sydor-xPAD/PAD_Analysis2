function [pedestal_img, p_mean, p_std] = fcn_dark_analysis(base_name, img_stack)
  pedestal_img = mean(img_stack, 3); # Simply an average of the dark frames
  p_mean = nanmean(pedestal_img(1:numel(pedestal_img)));
  p_std = nanstd(pedestal_img(1:numel(pedestal_img)));

  img_filename = [base_name "_pedestal.raw"];
  img_file = fopen(img_filename, "wb");
  fwrite(img_file, pedestal_img'(1:numel(pedestal_img)), "double", 0, "l");
  fclose(img_file);
  return
endfunction


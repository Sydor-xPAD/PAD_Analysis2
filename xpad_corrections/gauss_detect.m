clear

fg_filename = "/home/iainm/work/PAD_Analysis2/new_code/xpad_process/ihep_raw/run-s175_h2o-50us-dyncom-long-006/frames/s175_h2o-50us-dyncom-long-006_00000001.raw";

bg_filename = "/home/iainm/work/PAD_Analysis2/new_code/xpad_process/ihep_raw/run-s175_h2o-50us-backg-new/frames/s175_h2o-50us-backg-new_00000001.raw";

[fg_img num_frames] = read_xpad_image(fg_filename, 16, 256, 2048, 1024, 512, 20);
[bg_img num_frames] = read_xpad_image(bg_filename, 16, 256, 2048, 1024, 512, 20);

base_img = fg_img - bg_img;

slice = base_img(129:256,385:512,:);
slice = base_img((257+5):(384-5), (129+5):(256-5), :);

hist_hold = {};
bin_edge = {};
one_peak_fit = {};
one_peak_curve = {};
two_peak_fit = {};
two_peak_curve = {};
two_peak_neg_fit = {};
two_peak_neg_curve = {};
adj_peak = {};
r_squared_two_peak = {};
r_squared_neg_two_peak = {};
bin_centers = linspace(-50,100,51);
for cap_idx = 1:8
  [hist_hold{cap_idx} bin_edge{cap_idx}] = hist(vec(slice(:,:,cap_idx)), bin_centers);

  curr_hist = hist_hold{cap_idx};

  p0 = [max(curr_hist), std(vec(slice(:,:,cap_idx))), bin_centers(find(curr_hist == max(curr_hist))(1)), 0];
  p = lsqcurvefit(@gauss_1peak, p0, bin_centers, curr_hist);
  one_peak_fit{cap_idx}= p;

  one_peak_curve{cap_idx} = gauss_1peak(p, bin_centers);
  adj_peak{cap_idx} = curr_hist-one_peak_curve{cap_idx};

  p2_0 = [p0(1), 10, p0(3), p0(1), 10, p0(3)+40, 0];
  size(bin_centers)
  size(curr_hist)
  [p, my_resnorm, my_residuals] = lsqcurvefit(@gauss_2peak, p2_0, bin_centers, curr_hist);
  
  ss_res = my_resnorm;
  ss_tot = sum((curr_hist - mean(curr_hist)).^2);
  r_squared_two_peak{cap_idx} = 1-(ss_res/ss_tot);

  two_peak_fit{cap_idx} = p;
  two_peak_curve{cap_idx} = gauss_2peak(p, bin_centers);

  p2_0 = [p0(1), 10, p0(2), p0(1), 10, p0(2)-40, 0];
  size(bin_centers)
  size(curr_hist)
  [p, my_resnorm, my_residuals] = lsqcurvefit(@gauss_2peak, p2_0, bin_centers, curr_hist);
  ss_res = my_resnorm;
  ss_tot = sum((curr_hist - mean(curr_hist)).^2);
  r_squared_neg_two_peak{cap_idx} = 1-(ss_res/ss_tot);

  

  two_peak_neg_fit{cap_idx} = p;
  two_peak_neg_curve{cap_idx} = gauss_2peak(p, bin_centers);
   
  
endfor




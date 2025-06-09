function paired_stats = asbl_paired_img(img_stack, pair_array, stat_fcn)
  ## "pair" is a bit of a misnomer, and refers to a num of images averaged together
  num_img = size(img_stack)(3);
  paired_stats = 1:max(size(pair_array));
  stat_idx = 0;
  for img_per_pair=pair_array
    stat_idx = stat_idx+1;
    num_pair = floor(num_img/img_per_pair);
    stat_array = zeros(1,num_pair);
    for pair_idx=0:(num_pair-1)
      mean_img = mean(img_stack(:,:,(pair_idx*img_per_pair+1):((pair_idx+1)*img_per_pair)),3);
      mean_img = reshape(mean_img,1,[]);
      mean_img = mean_img(find(isfinite(mean_img)));
      if (numel(mean_img)) == 0
        stat_array(pair_idx+1) = NaN;
      else
        stat_array(pair_idx+1) = stat_fcn(mean_img, "omitnan");
      endif
    endfor
    paired_stats(stat_idx) = mean(stat_array);
  endfor
  return
endfunction


    
    

function bright_img = assemble_percentile_image(img, top_pctile)
  proc_image = sort(img,3);
  num_frames = size(proc_image)(3);
  start_idx = floor(top_pctile*num_frames)
  bright_img = mean(proc_image(:,:,start_idx:end),3);
  return;
endfunction

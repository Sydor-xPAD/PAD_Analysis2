function [stack, num_frames] = clip_avg_stack(img, num_skip_frames, num_caps)
  num_frames = size(img)(3)-num_skip_frames;
  img = img(:,:,(num_skip_frames+1):end);

  stack = per_cap_average(img, num_caps);
  return
endfunction

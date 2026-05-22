function bounce = calc_bounce(image_stack)
  bounce = -1;			# Start as invalid

  if (ndims(image_stack) < 3)
    bounce = 0;
    return
  endif
  
  num_frames = size(image_stack)(3);
  frame_mean = zeros(num_frames,1);
  for frame_idx=1:num_frames
    curr_pixels = reshape(image_stack(:,:,frame_idx),1,[]);
    curr_pixels = curr_pixels(find(isfinite(curr_pixels)));
    if isempty(curr_pixels)
      noise = -1;
      return
    endif
    frame_mean(frame_idx) = mean(curr_pixels);
  endfor

  bounce = std(frame_mean);
  return
endfunction

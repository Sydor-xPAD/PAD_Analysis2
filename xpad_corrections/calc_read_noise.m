function noise = calc_read_noise(image_stack, b_full_stack)

  if b_full_stack != 0          # Compute over stack as a whole
    pixels = reshape(image_stack,1,[]);
    pixels = pixels(find(isfinite(pixels)));
    
    if isempty(pixels)
      noise = -1;
    else
      noise = std(pixels);
    endif
    return
  else                          # Compute for each frame, then average
    num_frames = size(image_stack)(3);
    frame_noise = zeros(num_frames,1);
    for frame_idx=1:num_frames
      curr_pixels = reshape(image_stack(:,:,frame_idx),1,[]);
      curr_pixels = curr_pixels(find(isfinite(curr_pixels)));
      if isempty(curr_pixels)   # Entirely empty frame
        noise = -1;
        return;                 # Just abort
      endif
      frame_noise(frame_idx) = std(curr_pixels);
    endfor
    noise = mean(frame_noise);
    return;
  endif
endfunction


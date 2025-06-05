function bounce_array = calc_bounce_hist(img_stack)
  num_frames = size(img_stack)(3);
  bounce_array = zeros(1,num_frames);

  avg_frame = mean(img_stack,3); #Compute the average value across the stack

  for frame_idx=1:num_frames
    curr_frame = img_stack(:,:,frame_idx) - avg_frame;
    frame_mean = mean(reshape(curr_frame, 1, []));
    bounce_array(frame_idx) = frame_mean;
  endfor
  return
endfunction

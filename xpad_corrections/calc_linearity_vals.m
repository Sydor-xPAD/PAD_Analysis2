function [sigmasq, mu] = calc_linearity_vals(img_stack)
  if (ndims(img_stack) == 2)
    num_frames = 1;
  else
    num_frames=size(img_stack)(3);
  endif
  sigma_vals = zeros(num_frames, 1);
  mu_vals = zeros(num_frames, 1);

  for frame_idx=1:num_frames
    curr_pixels = reshape(img_stack(:,:,frame_idx),1,[]);
    curr_pixels = curr_pixels(find(isfinite(curr_pixels)));
    if isempty(curr_pixels)
      sigmasq = -1;
      mu = -1;
      return
    else
      sigma_vals(frame_idx) = std(curr_pixels)^2;
      mu_vals(frame_idx) = mean(curr_pixels);
    endif
  endfor

  sigmasq = mean(sigma_vals);
  mu = mean(mu_vals);
  return
endfunction

function ret = check_edge_unity(flatfield, asic_width, asic_height, num_caps)
  img_height = size(flatfield)(1);
  img_width = size(flatfield)(2);
  
  over_mask = zeros(size(flatfield));
  
  over_mask(1:asic_height:img_height,:) = 1; #Mask out the edge rows
  over_mask(asic_height:asic_height:img_height,:) = 1;
  over_mask(:, 1:(asic_width*2):img_width) = 1; #Mask out the columns - 2 ASIC/submodule
  over_mask(:, (asic_width*2):(asic_width*2):img_width) = 1;

  edge_pixels = find(over_mask);

  for cap_idx=1:num_caps
    curr_slice = flatfield(:,:,cap_idx);
    curr_edge = curr_slice(edge_pixels);
    valid_vals = xor(isnan(curr_edge), curr_edge == 1.0);
    if ! all(valid_vals)
      printf("Edge pixel neither unity nor NaN.\n");
      ret = -1;
      return;
    endif

  endfor
  
  ret = 0;
  return
endfunction

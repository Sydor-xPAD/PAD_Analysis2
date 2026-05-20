function ret = check_edge_val(base_mask, asic_width, asic_height)
  img_height = size(base_mask)(1);
  img_width = size(base_mask)(2);
  
  over_mask = ones(size(base_mask));
  
  over_mask(1:asic_height:img_height,:) = 0; #Mask out the edge rows
  over_mask(asic_height:asic_height:img_height,:) = 0;
  over_mask(:, 1:(asic_width*2):img_width) = 0; #Mask out the columns - 2 ASIC/submodule
  over_mask(:, (asic_width*2):(asic_width*2):img_width) = 0;

  full_mask = base_mask | over_mask;

  if ! all(full_mask)
    printf("Some edge pixels not masked out.");
    ret = 1;
    return
  endif

  ret = 0;
  return
endfunction

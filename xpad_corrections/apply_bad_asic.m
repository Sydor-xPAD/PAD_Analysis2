function img_stack = apply_bad_asic(asic_map, asic_height, asic_width, base_image)
  num_x_asic = size(base_image)(2)/asic_width;
  num_y_asic = size(base_image)(1)/asic_height;
  img_stack = base_image;
  
  for row_idx = 1:num_y_asic
    y_start = (row_idx-1)*asic_height+1;
    y_end = row_idx*asic_height;
    for col_idx = 1:num_x_asic
      x_start = (col_idx-1)*asic_width+1;
      x_end = col_idx*asic_width;

      if asic_map(row_idx,col_idx) != 0
        img_stack(y_start:y_end, x_start:x_end, :) = NaN;
      endif
    endfor
  endfor

  return
endfunction


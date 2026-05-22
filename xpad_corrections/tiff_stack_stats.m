clear

image_stack_name = "ihep-20250213/standard/dark_pixels_no_silver.tif";
out_stack_name = "dark_pixels.pgm";
  
image_stack = imread(image_stack_name,1:8);
    
collapsed_stack = sum(image_stack,3);
collapsed_stack = double(collapsed_stack!=0);

asic_w = 128;
asic_h = 128;

defect_raw = zeros(4,8);

asic_idx = 0;
for y_idx = 1:4
  row_lower = (y_idx-1)*asic_h+1;
  row_upper = y_idx*asic_h;
  for x_idx = 1:8
    asic_idx = asic_idx+1;
    col_lower = (x_idx-1)*asic_w+1;
    col_upper = x_idx*asic_w;
    curr_asic = collapsed_stack(row_lower:row_upper,col_lower:col_upper);
    defect_raw(y_idx,x_idx) = sum(reshape(curr_asic,1,[]));
  endfor
endfor

defect_frac = defect_raw/(128*128);

out_stack = double(image_stack);
out_stack(find(out_stack!=0)) = NaN;

pgm_write_stack(out_stack, out_stack_name, 8);
   

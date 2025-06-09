clear

base_grid = zeros(512,1024);

base_asic = zeros(128,128);

for x_idx=(64-4*11+1):11:(64+4*11+1)
  for y_idx=(64-4*11+1):11:(64+4*11+1)
    base_asic(y_idx,x_idx) = 1;
  endfor
endfor

for asic_x=1:8
  for asic_y=1:4
    start_row = (asic_y-1)*128+1;
    end_row = asic_y*128;
    start_col = (asic_x-1)*128+1;
    end_col = asic_x*128;
    base_grid(start_row:end_row,start_col:end_col) = base_asic;
  endfor
endfor


clear

base_grid = zeros(512,1024);
zero_grid = base_grid;

base_asic = zeros(128,128);

for x_idx=(64-4*11+1):11:(64+4*11+1)
  for y_idx=(64-4*11+1):11:(64+4*11+1)
    base_asic(y_idx,x_idx) = 1;
  endfor
endfor

## Expand to a multi-pixel shape
base_asic = filter2([0 1 0; 1 1 1; 0 1 0], base_asic);
base_asic = filter2([0 1 0; 1 1 1; 0 1 0], base_asic);
base_asic = sign(base_asic);
  
base_sm = [base_asic base_asic];
theta = -2.5*pi/180;
trans_matrix = [1 0 128; 0 1 64; 0 0 1]*[cos(theta) -sin(theta) 0; sin(theta) cos(theta) 0; 0 0 1]*[1 0 -128; 0 1 -64; 0 0 1];

rot_sm = zeros(128, 256);
for y=0:127
  for x=0:255
    coord_mat = [x y 1]';
    rot_coord = trans_matrix^-1*coord_mat;
    x_mod = floor(rot_coord(1)+1);
    y_mod = floor(rot_coord(2)+1);
    if (x_mod >= 1) & (x_mod <= 256) & (y_mod >= 1) & (y_mod <=128)
      rot_sm(y+1, x+1) = base_sm(y_mod, x_mod);
    endif
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

base_grid(1:128,1:256) = rot_sm;

## Now write out to files
imwrite(base_grid, "kega_gc_img_rot.tiff");

out_raw = fopen("kega_gc_img_rot.raw", "wb");

fwrite(out_raw, base_grid', "double", 0, "l");
fclose(out_raw);

out_raw = fopen("kega_blank.raw", "wb");
fwrite(out_raw, zero_grid', "double", 0, "l");
fclose(out_raw);

one_asic = base_grid;
one_asic(1:128,1:128) = 1;
out_raw = fopen("kega_one.raw", "wb");
fwrite(out_raw, one_asic', "double", 0, "l");
fclose(out_raw);

clear

my_array = ones(512,512,0);

for start_idx=0:7
  start_coord = 256+start_idx*20;
  my_array(start_coord:(start_coord+99),(start_coord):(start_coord+99),start_idx+1) = 2;
endfor

outfile = fopen('flat_square.raw', 'wb');

for slice_idx=1:8
  fwrite(outfile, my_array(:,:,slice_idx), 'double', 0, 'l');
endfor

fclose(outfile);

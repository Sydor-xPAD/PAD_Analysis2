function pgm_stack = pgm_read_stack(pgm_filename, num_caps)
  pgm_file = fopen(pgm_filename, 'rb');

  ## Read the header
  # XXX Skip the first two lines, assuming they are correct
  curr_line = fgetl(pgm_file)
  curr_line = fgetl(pgm_file)

  ## Read in the image sizes
  [img_width, img_height, maxval] = fscanf(pgm_file, " %i %i %i", "C")
  if (maxval > 255)
    disp("Maxval too high - PGM invalid")
  endif
                     # Read in the one whitespace following the maxval
  curr_pos = ftell(pgm_file);
  fclose(pgm_file);
  pgm_file = fopen(pgm_filename, "rb");
  fseek(pgm_file, curr_pos);
  fread(pgm_file, 1, "uint8");
  
  pgm_stack = uint8(zeros(img_height, img_width, num_caps)); #Initialize the stack

  for cap_idx=1:num_caps
    [pgm_frame, rcnt] = fread(pgm_file, [img_width img_height], 'uint8', 0);
    pgm_stack(:,:, cap_idx) = pgm_frame';
  endfor
  fclose(pgm_file)
  return
endfunction

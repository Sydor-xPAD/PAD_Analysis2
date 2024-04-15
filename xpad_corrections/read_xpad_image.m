function [img_stack, num_frames] = read_xpad_image(filename, bpp, offset, gap, width, height, MAX_FRAMES = 1005)
  ## Make the image to store into
  img_stack = zeros(height, width, MAX_FRAMES);
  
  img_file = fopen(filename, 'rb');

  data_pending = 1;
             %-=-= XXX Assumes there is at least one frame in the file

  ## Skip the offset
  fseek(img_file, offset, SEEK_SET);

  ## Read in the first slice according to datatype
  if bpp == 16
    data_type = 'uint16';
  elseif bpp == 32            #XXX May have issues later with float, but could use -32 for BPP like FITS doese
    data_type = 'uint32';
  endif

  [curr_array, nread_orig] = fread(img_file, [height, width], data_type, 0, 'l'); #-=-= XXX May need to change from big-endian to little endian at some point
  curr_array = curr_array';
  num_frames = 1;
  curr_array_orig = curr_array;
  
  fseek(img_file, gap, SEEK_CUR);

  img_stack(:,:,num_frames) = curr_array;
  
  while(data_pending == 1)
    ## Read in the data
    [curr_array, nread] = fread(img_file, [height, width], data_type, 0, 'l');
    curr_array = curr_array';

    disp("Reading frame: ")
    disp(num_frames+1)
    disp(nread)
    disp(nread_orig)
    disp(filename)
    disp(data_type)
    disp(offset)
    disp(gap)
    
    if (nread != height*width) || (num_frames >= MAX_FRAMES)   # Incomplete read or maximum frame count reached -- assume finish
      if (num_frames >= MAX_FRAMES)
        disp("WARNING: Maximum frame count reached.")
      endif
      data_pending = 0;
      img_stack(:,:,1);
      curr_array_orig;
      img_stack = img_stack(:,:,1:num_frames); #Truncate to frames actually read
      fclose(img_file);
      return                    # I guess we're done; maybe break vs return?
    endif

    num_frames++;                              #Increment the count
    img_stack(:,:,num_frames) = curr_array;    # Append the new slice
  
    fseek(img_file, gap, SEEK_CUR); # Skip the gap
  endwhile

  return
endfunction


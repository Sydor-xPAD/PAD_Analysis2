function [dark_mask, hot_mask, flatfield, errs] = load_corr_dir(corr_dir, num_caps)
  hotmask_name = 'hot_pixels.pgm';
  darkmask_name = 'dark_pixels.pgm';
  flatfield_name = 'flatfield.raw';

  errs = 0;

  hot_mask = imread([corr_dir '/' hotmask_name]);
  dark_mask = imread([corr_dir '/' darkmask_name]);
  flatfield = [];               #Set to a bad value to indicate problem, but still return

  if size(hot_mask) != size(dark_mask)
    printf("Hot pixel mask and dark pixel mask have different sizes.")
    errs = 1;
    return
  endif

  ff_file = fopen([corr_dir '/' flatfield_name], 'r');

  flatfield = zeros([size(hot_mask) num_caps]);
  
  for cap_idx = 1:num_caps
    [slice, count] = fread(ff_file, size(hot_mask)', "double", 0, "l");

    if count != numel(hot_mask)
      printf("Error: Flatfield file has insufficient data.\n")
      errs = 1;
      fclose(ff_file);
      return;
    endif

    flatfield(:,:,cap_idx) = slice'; #Transpose since read in column major
  endfor
  fclose(ff_file);

  return;
endfunction

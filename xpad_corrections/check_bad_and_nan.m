function ret = check_bad_and_nan(bad_mask, flatfield, num_caps)
    ret = 0;

    bad_pixels = find(bad_mask);
    good_pixels = find(!bad_mask);

    for cap_idx=1:num_caps
      curr_slice = flatfield(:,:,cap_idx);

      bad_vals = isnan(curr_slice(bad_pixels));
      
      if ! all(bad_vals)
        printf("Bad pixel not marked as NaN.\n");
        ret = -1;
      endif
      
      good_vals = isfinite(curr_slice(good_pixels));

      if ! all(good_vals)
        printf("Good pixel has non-finite value.\n");
        ret = -1;
      endif

    endfor
    
    return
endfunction

      
      

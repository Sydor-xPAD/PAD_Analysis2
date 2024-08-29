function full_ret = xpad_corr_sanity(base_outdir, num_caps, asic_width, asic_height)
  full_ret = 0
  std_dir = [base_outdir '/standard'];
  noedge_dir = [base_outdir '/no_edge'];
  unityedge_dir = [base_outdir '/unity_edge'];

  printf("Checking standard directory.\n");
  [dark_mask, hot_mask, flatfield, errs] = load_corr_dir(std_dir, num_caps);

  if errs != 0
    printf("Error loading standard directory.\n");
  endif

  combined_mask = dark_mask | hot_mask;
  ret = check_bad_and_nan(combined_mask, flatfield, num_caps);

  if ret
    printf("Error checking standard bad mask correspondence.\n");
  endif

  full_ret = bitor(full_ret, ret);

  clear dark_mask hot_mask flatfield
  printf("Checking no-edge directory.\n");
  [dark_mask, hot_mask, flatfield, errs] = load_corr_dir(noedge_dir, num_caps);

  if errs
    printf("Error loading no-edge directory.\n");
  endif
  
  combined_mask = dark_mask | hot_mask;
  ret = check_bad_and_nan(combined_mask, flatfield, num_caps);

  if ret
    printf("Error checking no-edge bad mask correspondence.\n");
  endif

  full_ret = bitor(full_ret, ret);

  ret = check_edge_val(dark_mask, asic_width, asic_height);
  if ret
    printf("Error checking no-edge dark mask edge pixels.\n");
  endif

  full_ret = bitor(full_ret, ret);
  ret = check_edge_val(hot_mask, asic_width, asic_height);
  if ret
    printf("Error checking no-edge hot mask edge pixels.\n");
  endif

  full_ret = bitor(full_ret, ret);


  clear dark_mask hot_mask flatfield
  printf("Checking unity-edge directory.\n");
  [dark_mask, hot_mask, flatfield, errs] = load_corr_dir(unityedge_dir, num_caps);

  if errs
    printf("Error loading unity-edge directory.\n");
  endif

  combined_mask = dark_mask | hot_mask;
  ret = check_bad_and_nan(combined_mask, flatfield, num_caps);

  if ret
    printf("Error checking unity-edge bad mask correspondence.\n");
  endif

  full_ret = bitor(full_ret, ret);

  ret = check_edge_unity(flatfield, asic_width, asic_height, num_caps);

  if ret
    printf("Bad unity-edge pixel gain detected.\n");
  endif

  full_ret = bitor(full_ret, ret);
  
endfunction
    

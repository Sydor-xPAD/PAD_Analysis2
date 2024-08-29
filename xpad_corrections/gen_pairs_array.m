function pairs = gen_pairs_array(max_pairs)
  if max_pairs <= 0
    pairs = 0;
    return
  endif

  max_pairs = floor(max_pairs);
  p2 = floor(log2(max_pairs));

  if log2(max_pairs) == p2
    pairs = 2.^(0:p2);
  else
    pairs = [2.^(0:p2) max_pairs];
  endif

  ## Now add in the square
  max_square = floor(sqrt(max_pairs));
  sq_array = (1:max_square).^2;
  pairs = unique([pairs sq_array]);
  return
endfunction

  
    

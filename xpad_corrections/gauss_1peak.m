function y = gauss_1peak(p,x)
  ## Unpack parameters

  p_scale = p(1);
  p_sigma = p(2);
  p_mean = p(3);
  dc = p(4);

  p_sigma=abs(p_sigma);

  y = p_scale*1./sqrt(2*pi*p_sigma)*exp(-(x-p_mean).^2/(2*p_sigma.^2)) + dc;

  return 
  

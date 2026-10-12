function y = gauss_2peak(p,x)
  ## Unpack parameters

  # Intialize arrays
  p_scale = zeros(2,1);
  p_sigma = zeros(2,1);
  p_mean = zeros(2,1);

  # Do the unpacking proper
  p_scale(1) = abs(p(1));
  p_sigma(1) = abs(p(2));
  p_mean(1) = p(3);

  p_scale(2) = abs(p(4));
  p_sigma(2) = abs(p(5));
  p_mean(2) = p(6);

  dc = p(7);

  peak_array = zeros(numel(x), 2);
  for peak_idx = 1:2
    peak(:,peak_idx) = p_scale(peak_idx) * 1./sqrt(2*pi*p_sigma(peak_idx)^2)*exp(-(x-p_mean(peak_idx)).^2/(2*p_sigma(peak_idx)^2));
  endfor

  y = (peak(:,1)+peak(:,2)+dc)';
  return

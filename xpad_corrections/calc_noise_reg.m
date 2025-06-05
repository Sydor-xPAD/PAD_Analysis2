function [coeff, pred_y] = calc_noise_reg(x_val, y_val)
  x_val = x_val(1:numel(x_val));
  y_val = y_val(1:numel(y_val)); #Reshape to row vectors

  x_reg = [x_val'*0+1 1./sqrt(x_val')];
  coeff = (x_reg'*x_reg)^-1*x_reg'*y_val';
  pred_y = coeff(1)+coeff(2)./sqrt(x_val);
  return
endfunction


  

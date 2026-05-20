function bound_struct = calc_bounds(asic_idx, img_struct)
    asic_x_idx = mod(asic_idx, img_struct.num_x_asics);
    asic_y_idx = floor(asic_idx / img_struct.num_x_asics);
    
    bound_struct.x_base_min = asic_x_idx * img_struct.asic_width + 1;
    bound_struct.x_base_max = (asic_x_idx+1)*img_struct.asic_width;
    bound_struct.y_base_min = asic_y_idx * img_struct.asic_height + 1;
    bound_struct.y_base_max = (asic_y_idx+1)*img_struct.asic_height;
    bound_struct.x_margin_min = bound_struct.x_base_min + img_struct.x_margin;
    bound_struct.x_margin_max = bound_struct.x_base_max - img_struct.x_margin;
    bound_struct.y_margin_min = bound_struct.y_base_min + img_struct.y_margin;
    bound_struct.y_margin_max = bound_struct.y_base_max - img_struct.y_margin;

    return
endfunction

function [line_cell, file_ok] = get_config_line(fid)
  line_cell = cell(1,2);
  file_ok = 1;
  line_count = 1;
  curr_line = fgetl(fid);        #Read the next line
  while(ischar(curr_line))
    trim_line = strtrim(curr_line);
    size(trim_line);
    if (isempty(trim_line) || (trim_line(1) == '#') || (trim_line(1) == '['))
      curr_line = fgetl(fid);
      continue
    endif

    split_line = textscan(trim_line, "%s %s", "Delimiter", "=");
    if (isempty(split_line{1,1}{1,1}) || isempty(split_line{1,2}{1, 1}))
      file_ok = 0;
    endif

    line_cell{line_count, 1} = split_line{1,1};
    line_cell{line_count, 2} = split_line{1,2};

    line_count = line_count + 1;

    curr_line = fgetl(fid);
  endwhile
    
  return

    

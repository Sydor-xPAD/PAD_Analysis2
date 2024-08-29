clear

output_dir = 'airbox_1433';
perform_test = 0;
std_dir = [output_dir '/standard'];
noedge_dir = [output_dir '/no_edge'];
unityedge_dir = [ output_dir '/unity_edge'];

printf("Note: It is assumed that for flatfield calculations that dark_mask_filename and hot_mask_filename are set for the output names from gen_bad_mask.m\n");
printf("As configured, this program uses slope calculation for dark pixels.\n");

printf("Also make sure you have set the output directory in this file.\n");
printf("Output directory set for \"%s\"\nExisting files will be clobbered.\n", output_dir);
printf("*****************************\n");
input("Press Enter when ready.", "s");

save("corr_gen_param.octave");

printf("Creating output directories.\n");
mkdir(output_dir);
mkdir(std_dir);
mkdir(noedge_dir);
mkdir(unityedge_dir);

printf("Generating bad pixel masks.\n");
printf("Generating standard masks.\n");
gen_bad_mask;
load corr_gen_param.octave
copyfile("dark_pixels.pgm", [std_dir '/dark_pixels_val.pgm']);
copyfile("dark_pixels.pgm", [unityedge_dir '/dark_pixels_val.pgm']);
gen_dark_mask;
load corr_gen_param.octave
copyfile("dark_pixels.pgm", std_dir);
copyfile("hot_pixels.pgm", std_dir);

## Unity edge uses the same bad-pixel masks as the standard set
copyfile("dark_pixels.pgm", unityedge_dir);
copyfile("hot_pixels.pgm", unityedge_dir);

printf("Generating No-Edge masks.\n");
filter_edge = 1;
gen_bad_mask;
load corr_gen_param.octave
copyfile("dark_pixels.pgm", [noedge_dir "/dark_pixels_val.pgm"]);
filter_edge = 1;
gen_dark_mask;
load corr_gen_param.octave
copyfile("dark_pixels.pgm", noedge_dir);
copyfile("hot_pixels.pgm", noedge_dir);

printf("Handling Unity-Edge masks.\n");
## Done, as described above

printf("Finished generating bad pixel masks.\n");
printf("*******************************\n");
printf("Generating flat-field maps.\n");

printf("Generating standard map.\n");
## First we need the standard bad pixel masks
copyfile([std_dir '/*.pgm'], ".");
clear filter_edge               # No special handling of edge pixels
create_flatfield;
load corr_gen_param.octave
copyfile('flatfield.raw', std_dir);

printf("Generating Unity-Edge map.\n");
filter_edge = 1;
create_flatfield;
load corr_gen_param.octave
copyfile('flatfield.raw', unityedge_dir);

printf("Generating No-Edge map.\n");
clear filter_edge
copyfile([noedge_dir '/*.pgm'], "."); #Need the no-edge mask to NaN out the edge pixels in the flatfield
create_flatfield;
load corr_gen_param.octave
copyfile('flatfield.raw', noedge_dir);

if perform_test != 0
  printf("Running sanity test.\n");
  ret = xpad_corr_sanity(output_dir);

  if ret != 0
    printf("Error in sanity test.\n");
  endif
endif

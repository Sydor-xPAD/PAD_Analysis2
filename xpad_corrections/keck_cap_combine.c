#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
  FILE *in_img[8];
  char *img_frame;
  int img_idx;
  size_t img_size = 512*512*2+1024;
  FILE *out_img;
  int frame_count;
  size_t io_count;

  img_frame = malloc(img_size);
  out_img = fopen("flat_img.raw", "wb");

  for (img_idx = 0; img_idx < 8; img_idx++)
    {
      in_img[img_idx] = fopen(argv[img_idx+1], "rb");
      printf("%s\n", argv[img_idx+1]);
    }

  
  frame_count = 0;
  while (1)
  {
      for (img_idx = 0; img_idx < 8; img_idx++)
      {
          io_count = fread(img_frame, img_size, 1, in_img[img_idx]);
          if (io_count != 1)
          {
              fprintf(stderr, "Error reading frame %i in file # %i.\n", frame_count, img_idx);
              goto finish_read;
          }
          io_count = fwrite(img_frame, img_size, 1, out_img);
          if (io_count != 1)
          {
              fprintf(stderr, "Error writing frame %i in file # %i.\n", frame_count, img_idx);
              goto finish_read;
          }

          if (feof(in_img[img_idx]))
          {
              fprintf(stderr, "Reached EOF in file # %i.\n", img_idx);
          }
      }
      frame_count++;
  }

finish_read:
  printf("Successfully read %i frames.\n", frame_count);
          
  return 0;
}


	 
  

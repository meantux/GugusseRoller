#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <ctype.h>
#include <jpeglib.h>
#include <math.h>
#include <limits.h>

#ifndef true
#define true (-1)
#define false 0
#endif


char *usage="img2snd <approx true height in pixels> [-mono] <file1.jpg> [<file2.jpg>] [...]\n";

     typedef struct {
	  char *fn;
	  int width;
	  int height;
	  int serial;
	  unsigned char *data;
     }Image;

typedef struct {
     short *data;
     int size;
}SoundFrame;



static void releaseImage(Image *im)
{
     // printf("Releasing %p\n", im);
     if (im==NULL)return;
     if (im->data!=NULL) free(im->data);
     im->data=NULL;
     if (im->fn != NULL) free(im->fn);
     free(im);
}

Image *readjpg(char *fn)
{ 
     FILE *in;
     int i,bytecount;
     Image *res;
     unsigned long location=0;
     unsigned char *ptr;
     struct jpeg_decompress_struct cinfo={0};
     struct jpeg_error_mgr jerr;
     JSAMPROW row_pointer[1];
     //printf("openImage(%s);\n", fn);
     if((in=fopen(fn, "rb"))==NULL)
     {
	  fprintf(stderr, "Could not open %s for reading\n", fn);
	  return NULL;
     }
     if((res=malloc(sizeof(Image)))==NULL)
     {
	  fprintf(stderr, "Out of memory, could not alloc small struct\n");
	  fclose(in);
	  return NULL;
     }
     memset(res, 0, sizeof(Image)); 
     cinfo.err = jpeg_std_error(&jerr);
     jpeg_create_decompress(&cinfo);
     jpeg_stdio_src(&cinfo, in);
     if(jpeg_read_header(&cinfo, true)!=JPEG_HEADER_OK)
     {
	  fprintf(stderr, "Error reading jpeg header of %s\n", fn);
	  free(res);
	  return NULL;
     }
     res->width=cinfo.image_width;
     res->height=cinfo.image_height;
     //printf("jpeg_read_header returned JPEG_HEADER_OK with image_width=%d and image_height=%d\n", res->width, res->height);
     //  printf("about to start decompress\n");
     jpeg_start_decompress( &cinfo );
     if((res->data=malloc(cinfo.output_width * cinfo.output_height * cinfo.num_components ))==NULL)
     {
	  fprintf(stderr, "Out of memory, could not load picture %s with its %d x %d pixels\n", fn, res->width, res->height);
	  jpeg_finish_decompress(&cinfo);
	  free(res);
	  return NULL;
     }
     // printf("about to alloc a row\n");
     if((row_pointer[0] = (unsigned char *)malloc( cinfo.output_width*cinfo.num_components ))==NULL)
     {
	  fprintf(stderr, "Out of memory, could not allocate row pointer\n");
	  free(res->data);
	  free(res);
	  jpeg_finish_decompress(&cinfo);
	  return NULL;
     }
     // printf("about to scan\n");
     while( cinfo.output_scanline < res->height )
     {
	  jpeg_read_scanlines( &cinfo, row_pointer, 1 );
	  for( i=0; i<res->width*cinfo.num_components;i++) 
	       res->data[location++] = row_pointer[0][i];
     }
     free(row_pointer[0]);
     // printf("checking num_components\n");
     if(cinfo.num_components==1)
     {
	  // for speed performance issue at resizing we'll convert now monochromous jpgs in RGBs
	  bytecount=cinfo.output_width * cinfo.output_height * 3;
	  if((ptr=malloc(bytecount))==NULL)
	  {
	       fprintf(stderr, "Out of memory, could not load picture %s with its %d x %d pixels\n", fn, res->width, res->height);
	       jpeg_finish_decompress(&cinfo);
	       free(res->data);
	       free(res);
	       return NULL;
	  }
	  for (i=0;i<bytecount;i++)
	  {
	       ptr[i]=res->data[i/3];
	  }
	  free(res->data);
	  res->data=ptr;
     }
     // printf("About to fclose(in);\n");
     fclose(in);
     res->fn=strdup(fn);
     // printf("About to finish_decompress;\n");
     jpeg_finish_decompress(&cinfo);
     // printf("About to return with res=%p and res->data=%p\n", res, res->data);
     return res;
}

SoundFrame *imageToSoundFrame(char *fn){      
     int val, x, y, offset, min, max, mid = -1;
     unsigned int *ligne=NULL;
     SoundFrame *sf;
     Image *im;
     im=readjpg(fn);
     ligne=(int *)malloc(im->width*sizeof(int));
     sf=(SoundFrame *)malloc(sizeof(SoundFrame));
     sf->data=(short *)malloc(sizeof(short)*im->height);
     sf->size=im->height;
     offset=0;
     for (y=0; y<im->height;y++){
	  min=9999999;
	  max=0;
	  for (x=0;x<im->width;x++){
	       ligne[x]=im->data[offset++];
	       ligne[x]+=im->data[offset++];
	       ligne[x]+=im->data[offset++];
	       if (ligne[x] > max)max=ligne[x];
	       if (ligne[x] < min)min=ligne[x];
	  }
	  if (mid == -1){mid=(min+max)/2;}
	  val=0;
	  for (x=0;x<im->width;x++){
	       if (ligne[x]>mid)val++;
	  }
	  sf->data[y]=val;
	  //fwrite(&val, sizeof(val), 1, rawsnd);
	  //fprintf(rawsnd, "%d\n", val);
     }
     releaseImage(im);
     return sf;
}


int matchSeam(SoundFrame *prev, SoundFrame *next, int approx){
  int range, aval, bval, difference;
  int inMatchIdx, lowest_idx=0, lowest_val = 2000000000;
  int jeu, offset, matchwidth;
  jeu=prev->size-approx;
  matchwidth=jeu/2;
  
  for(offset=0;offset<((jeu * 2)-matchwidth); offset++){
    difference=0;
    for(inMatchIdx=0;inMatchIdx<matchwidth;inMatchIdx++){
      aval=prev->data[inMatchIdx+prev->size-matchwidth];
      bval=next->data[offset+inMatchIdx];
      difference+=abs(aval-bval);	 
    }
    if (difference < lowest_val){
      lowest_idx=offset;
      lowest_val=difference;
    }
  }

  printf("We matched at offset %d\n", lowest_idx);
  for(inMatchIdx=0;inMatchIdx<matchwidth;inMatchIdx++){
    aval=prev->data[inMatchIdx+prev->size-matchwidth];
    bval=next->data[lowest_idx+inMatchIdx];
    next->data[lowest_idx+inMatchIdx]=(bval * inMatchIdx / matchwidth) + (aval * (matchwidth - inMatchIdx - 1)/matchwidth);
  }
  
  return (lowest_idx);
}


void serializeData(SoundFrame *frame, int approx, FILE *out){
     static int totalSamples=0;
     static int frames=0;
     static SoundFrame* sfprev=NULL;
     int skip, matchwidth;
     matchwidth=(frame->size-approx)/2;
     if (sfprev == NULL){
	  sfprev=frame;
	  frames++;
	  totalSamples=frame->size;
	  fwrite(frame->data, sizeof(short), frame->size-matchwidth, out);
	  return;
     }
     skip=matchSeam(sfprev, frame, approx);
     fwrite(&frame->data[skip],sizeof(short), frame->size-skip-matchwidth, out);
     frames++;
     totalSamples+= frame->size-skip-matchwidth;
     printf("Frame #%05d, skipping %d\n", frames, skip);
     printf("sox -r %d -e signed-integer -b 16 -c 1 left.raw out.wav\n", (24 * totalSamples)/frames);
     free(sfprev->data);
     free(sfprev);
     sfprev=frame;     
}

int main (int argc, char *argv[]){
     int argidx=2;
     int mono=0;
     int approx;
     SoundFrame *prev=NULL, *sf;
     FILE *rawsnd;
     approx=atoi(argv[1]);
     rawsnd=fopen("left.raw", "wt");
     while (argidx < argc){
	  if (strcmp(argv[argidx], "-mono")==0){
	       mono= -1;
	  }else{
	       sf=imageToSoundFrame(argv[argidx]);
	       serializeData(sf, approx, rawsnd);
	  }
	  argidx++;
     }
     fclose(rawsnd);

}

// HOW TO CONVERT THE RESULTING DATA IN WAV
//sox -r 30384 -e signed-integer -b 16 -c 1 left.raw out.wav
// Be sure the very first line of the first image has the righ colors

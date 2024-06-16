#include <stdlib.h>
#include <stdint.h>
#include <time.h>


inline uint16_t getPixValue(const uint8_t *buf, int pixelOffset) {
    int byteOffset = pixelOffset * 3 / 2;
    uint16_t lowerPart, upperPart;

    if (pixelOffset % 2 == 0) { 
        // Pixel starts at beginning of a byte
        lowerPart = buf[byteOffset];
        upperPart = buf[byteOffset + 1] & 0x0F;
	return (upperPart << 8) | lowerPart; 
    } else {
        // Pixel starts in the middle of a byte
      lowerPart = buf[byteOffset] & 0xF0;
      upperPart = buf[byteOffset + 1];
      return(upperPart << 4) | (lowerPart >> 4);
    }
}


void draw_histogram(uint8_t *buffer, int width, int height, int x, int y) {
    // Seed the random number generator (only need to do this once)
    //static int seeded = 0;
    int i,j;
    //if (!seeded) {
    //    srand(time(NULL)); // Seed with current time
    //    seeded = 1;
    //}


    int buffer_size=width * height * 4;

    
    
    for (i=0;i<width;i+=1){
        for (j=0;j<height;j+=10){
            // Calculate pixel index in RGB32 buffer (3 bytes per pixel)
            int pixelIndex = (j * width + i) * 4; 
	
            // Ensure we don't go out of bounds
            if (pixelIndex >= 0 && pixelIndex < buffer_size) {
            // Set pixel to white (RGB: 255, 255, 255)
                buffer[pixelIndex] = 255; // Blue
                buffer[pixelIndex + 1] = 255; // Green
                buffer[pixelIndex + 2] = 255; // Red 
            }
        }
    } 

    //int pixelIndex= (y*width+x)*4;
    //if (pixelIndex >= 0 && pixelIndex < buffer_size) {
    //  buffer[pixelIndex] = 255; // Blue
    //  buffer[pixelIndex + 1] = 255; // Green
    //  buffer[pixelIndex + 2] = 255; // Red
    //}
    
}



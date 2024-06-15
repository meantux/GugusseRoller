#include <stdlib.h>
#include <time.h>

void draw_histogram(unsigned char *buffer, int width, int height) {
    // Seed the random number generator (only need to do this once)
    static int seeded = 0;
    int i,j;
    if (!seeded) {
        srand(time(NULL)); // Seed with current time
        seeded = 1;
    }


    int buffer_size=width * height * 3;

    for (i=0;i<width;i+=1){
        for (j=0;j<height;j+=10){
            // Calculate pixel index in RGB32 buffer (3 bytes per pixel)
            int pixelIndex = (j * width + i) * 3; 
	
            // Ensure we don't go out of bounds
	    if (pixelIndex >= 0 && pixelIndex < buffer_size) {
            // Set pixel to white (RGB: 255, 255, 255)
                buffer[pixelIndex] = 255; // Blue
		buffer[pixelIndex + 1] = 255; // Green
		buffer[pixelIndex + 2] = 255; // Red 
	    }
	}
    }
}

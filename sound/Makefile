
build:
	gcc -g -o img2snd img2snd.c -ljpeg

clean:
	rm -fr img2snd *.wav *.raw

test:	build
	echo The number 160 represents  an approximation of the number of overlayed lines
	echo between a frame and the next one
	echo ""
	./img2snd 160 images/*.jpg

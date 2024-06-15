CC = gcc
CFLAGS = -shared -fPIC 

histogram_lib.so: histogram_lib.c
	$(CC) $(CFLAGS) -o $@ $<

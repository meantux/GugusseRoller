#!/usr/bin/python

import picamera
import picamera.array
import numpy as np

with picamera.PiCamera() as camera:
    camera.resolution = (1280, 720)
    camera.awb_mode = 'off'
    # Start off with ridiculously low gains
    rg, bg = (0.5, 0.5)
    camera.awb_gains = (rg, bg)
    with picamera.array.PiRGBArray(camera) as output:
        # Allow 30 attempts to fix AWB
        camera.zoom=(0.45,0.45,0.55,0.55)
        for i in range(300):
            # Capture a tiny resized image in RGB format, and extract the
            # average R, G, and B values
            
            camera.capture(output, format='rgb', use_video_port=True)
            r, g, b = (np.mean(output.array[..., i]) for i in range(3))
            print('R:%5.2f, B:%5.2f = (%5.2f, %5.2f, %5.2f)' % (
                rg, bg, r, g, b))
            # Adjust R and B relative to G, but only if they're significantly
            # different (delta +/- 2)
            if abs(r - g) > 0.1:
                if r > g:
                    rg -= 0.01
                else:
                    rg += 0.01
            if abs(b - g) > 0.1:
                if b > g:
                    bg -= 0.01
                else:
                    bg += 0.01
            camera.awb_gains = (rg, bg)
            output.seek(0)
            output.truncate()

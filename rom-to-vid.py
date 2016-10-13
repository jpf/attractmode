#!/usr/bin/env python
# PLAYING WITH LIBRETRO FROM PYTHON
# Can I just build a dumb video in memory???

import sys
import nostalgiapile


CORE_LIBRARY_PATH = ("/Applications/RetroArch.app"
                     "/Contents/Resources/cores/snes9x2010_libretro.dylib")
ROM_PATH = sys.argv[1]

# Nice set of frames:
frame_start = 353
duration_seconds = 2

emu = nostalgiapile.Emulator(CORE_LIBRARY_PATH)
emu.load_game(ROM_PATH)

def make_frame(t):
    global emu
    emu.next()
    return emu.frame.to_numpy_array()


while emu.frame_number < frame_start:
    emu.next()

from moviepy.editor import VideoClip
print "Creating video now ..."
clip = VideoClip(make_frame, duration=duration_seconds)
fps = emu.config['av_info']['fps']
clip.write_videofile("anim.mp4", fps=fps)

emu.stop()

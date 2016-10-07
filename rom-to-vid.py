#!/usr/bin/env python
# PLAYING WITH LIBRETRO FROM PYTHON
# Can I just build a dumb video in memory???

import sys
import numpy as np
import nostalgiapile


CORE_LIBRARY_PATH = ("/Applications/RetroArch.app"
                     "/Contents/Resources/cores/snes9x_next_libretro.dylib")
ROM_PATH = sys.argv[1]

# Nice set of frames:
frame_start = 353
frame_end = frame_start + 6000  # 30

step = 0

emu = nostalgiapile.Emulator(CORE_LIBRARY_PATH)
emu.load_game(ROM_PATH)


def next_frame():
    global step
    global emu
    emu.core.retro_run()
    step += 1
    framebuffer = nostalgiapile.video_q.get()
    return framebuffer


def make_frame(t):
    framebuffer = next_frame()
    arr = np.frombuffer(
        framebuffer,
        dtype=np.uint16,
        count=512*1024
    ).reshape((512, 1024))[0:224, 0:256].astype(np.uint32)
    screen = np.zeros((224, 256, 3), dtype=np.uint8)
    screen[:, :, 0] = (arr & 0xF800) >> 8
    screen[:, :, 1] = (arr & 0x07E0) >> 3
    screen[:, :, 2] = (arr & 0x001F) << 3
    return screen

while step < frame_start:
    next_frame()

from moviepy.editor import VideoClip
print "Creating video now ..."
clip = VideoClip(make_frame, duration=60)
fps = emu.config['av_info']['fps']
clip.write_videofile("anim.mp4", fps=fps)

emu.core.retro_unload_game()
emu.core.retro_deinit()

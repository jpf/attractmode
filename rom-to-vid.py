#!/usr/bin/env python
#
# Given a libretro core and SNES ROM, write a video of what that game
# would look like if left playing without pressing buttons for
# (by default) 10 minutes.
#
# Usage:
#   rom-to-vid.py snes9x ./SuperGame.smc
import sys

from moviepy.editor import VideoClip
import nostalgiapile


CORE_LIBRARY_PATH = ("/Applications/RetroArch.app"
                     "/Contents/Resources/cores/"
                     "{}_libretro.dylib".format(sys.argv[1]))
ROM_PATH = sys.argv[2]
frame_start = 0
duration_seconds = 600

output_file = ROM_PATH + ".mp4"
print "Output file: ", output_file

if len(sys.argv) > 3:
    frame_start = int(sys.argv[3])

print "Core: {}".format(CORE_LIBRARY_PATH)
emu = nostalgiapile.Emulator(CORE_LIBRARY_PATH)
emu.load_game(ROM_PATH)


def make_frame(t):
    global emu
    # print "frame: ", emu.frame_number
    emu.next()
    return emu.frame.to_numpy_array()


while emu.frame_number < frame_start:
    emu.next()

print "Creating video starting at frame # {} ...".format(frame_start)
clip = VideoClip(make_frame, duration=duration_seconds)
clip.write_videofile(output_file, fps=emu.config['av_info']['fps'])

emu.stop()

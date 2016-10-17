from moviepy.editor import VideoFileClip
import pprint
import sys
import numpy as np

videofile = sys.argv[1]
clip = VideoFileClip(videofile)

found = []
last_timestamp = 0
for timestamp, frame in clip.iter_frames(with_times=True):
    if np.count_nonzero(frame) != 0:
        continue
    if timestamp - last_timestamp > 0.1:
        found.append(last_timestamp)
        found.append(timestamp)
    last_timestamp = timestamp

scene = 1
for i in range(0,len(found),2):
    start, end = found[i], found[i+1]
    subclip = clip.subclip(start, end)
    print "{},{}".format(start, end)
    filename = "scene{}.mp4".format(scene)
    print "Writing {}".format(filename)
    subclip.write_videofile(filename)
    scene += 1

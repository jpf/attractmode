import hashlib
import pprint
import sys

from PIL import Image
from moviepy.editor import VideoFileClip
import imagehash
import numpy as np

videofile = sys.argv[1]
vidclip = VideoFileClip(videofile)

last_timestamp = 0
clip = list()
scene = 1
found_scenes = {}
similar = {}

# This is a number I came up with on my own
# It should probably be based on the size of the scene we are looking at
fudge_factor = 400

allowable_skew = 10 # frames

for timestamp, frame in vidclip.iter_frames(with_times=True):
    if np.count_nonzero(frame) != 0:
        # if len(clip) >= 20:
        #     continue
        frame_hash = imagehash.phash(Image.fromarray(frame))
        if str(frame_hash).startswith('000000000000000'):
            continue
        clip.append(frame_hash)
        continue
    if timestamp - last_timestamp > 0.1:
        scene_id = "scene{0:03d}".format(scene)
        scene_thumb = np.array(clip)
        found = False
        for other_id in found_scenes:
            if found:
                continue
            other_thumb = found_scenes[other_id]
            aa = other_thumb
            bb = scene_thumb
            a = aa
            b = bb
            len_a = len(aa)
            len_b = len(bb)
            if abs(len_a - len_b) > allowable_skew:
                continue
            if len_a > len_b:
                a = aa[:len_b]
            else:
                b = bb[:len_a]
            try:
                delta = np.sum(a - b)
            except:
                # Debug:
                rv_a = "".join([str(x) for x in a])
                rv_b = "".join([str(x) for x in b])
                print "ERROR: \n'{}' != \n'{}'".format(rv_a, rv_b)
                sys.exit(10)
            print "{}({}) - {}({}) = {}".format(
                other_id, len_a,
                scene_id, len_b,
                delta)
            if delta < fudge_factor:
                similar[other_id].append(scene_id)
                found = True
                # pprint.pprint(similar)
        if not found:
            similar[scene_id] = []
            found_scenes[scene_id] = scene_thumb
        scene += 1
        clip = list()
    last_timestamp = timestamp

pprint.pprint(similar)
sys.exit(0)
for scene_id in found_scenes.keys():
    pthumb = "".join([str(x) for x in found_scenes[scene_id]])
    print "{}\t{}".format(scene_id, pthumb)

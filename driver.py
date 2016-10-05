# PLAYING WITH LIBRETRO FROM PYTHON
# Can I just build a dumb video in memory???

import sys
import os
import signal

# visualization
# import matplotlib.pyplot as plt
import numpy as np

# We'll use ctypes to access the libretro C API exposed by the
# snes9x_next core
from ctypes import (CFUNCTYPE,
                    POINTER,
                    Structure,
                    byref,
                    c_bool,
                    c_byte,
                    c_char,
                    c_char_p,
                    c_double,
                    c_float,
                    c_int,
                    c_short,
                    c_size_t,
                    c_uint,
                    c_ushort,
                    c_void_p,
                    cast,
                    cdll)


# structs from libretro.h
class retro_variable(Structure):
    _fields_ = [("key", c_char_p),
                ("value", c_char_p)]


class retro_game_info(Structure):
    _fields_ = [("path", c_char_p),
                ("data", c_void_p),
                ("size", c_size_t),
                ("meta", c_char_p)]


class retro_input_descriptor(Structure):
    _fields_ = [("port", c_uint),
                ("device", c_uint),
                ("index", c_uint),
                ("id", c_uint),
                ("description", c_char_p)]


class retro_system_info(Structure):
    _fields_ = [("library_name", c_char_p),
                ("library_version", c_char_p),
                ("valid_extensions", c_char_p),
                ("need_fullpath", c_bool),
                ("block_extract", c_bool)]


class retro_game_geometry(Structure):
    _fields_ = [("base_width", c_uint),
                ("base_height", c_uint),
                ("max_width", c_uint),
                ("max_height", c_uint),
                ("aspect_ratio", c_float)]


class retro_system_timing(Structure):
    _fields_ = [("fps", c_double),
                ("sample_rate", c_double)]


class retro_system_av_info(Structure):
    _fields_ = [("geometry", retro_game_geometry),
                ("timing", retro_system_timing)]

CORE_LIBRARY_PATH = "snes9x_next_libretro.dylib"
ROM_PATH = sys.argv[1]

RETRO_ENVIRONMENT_GET_OVERSCAN = 2
RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL = 8
RETRO_ENVIRONMENT_SET_PIXEL_FORMAT = 10
RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS = 11
RETRO_ENVIRONMENT_SET_VARIABLES = 16
RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE = 17
RETRO_ENVIRONMENT_GET_LOG_INTERFACE = 27
RETRO_ENVIRONMENT_SET_CONTROLLER_INFO = 35
RETRO_ENVIRONMENT_SET_SUPPORT_ACHIEVEMENTS = 65578

RETRO_PIXEL_FORMAT_RGB565 = 2


# Python functions wrapped as C function pointers
@CFUNCTYPE(c_bool, c_uint, c_void_p)
def environ_cb(cmd, data):
    if cmd == RETRO_ENVIRONMENT_GET_OVERSCAN:
        pass
    elif cmd == RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL:
        level = cast(data, POINTER(c_uint)).contents.value
        assert level == 7
    elif cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        print "PIXEL FORMAT"
        format = cast(data, POINTER(c_int)).contents.value
        print "pixel format:", format
        assert format == RETRO_PIXEL_FORMAT_RGB565
        return True
    elif cmd == RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
        descriptors = cast(data, POINTER(retro_input_descriptor))
        i = 0
        while descriptors[i].description:
            d = descriptors[i]
            print d.port, d.device, d.index, d.id, d.description
            i += 1
    elif cmd == RETRO_ENVIRONMENT_SET_VARIABLES:
        print "VARIABLES"
        variables = cast(data, POINTER(retro_variable))
        i = 0
        while variables[i].key:
            v = variables[i]
            print v.key, "::", v.value
            i += 1
    elif cmd == RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        pass
    elif cmd == RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
        pass
    elif cmd == RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
        pass
    elif cmd == RETRO_ENVIRONMENT_SET_SUPPORT_ACHIEVEMENTS:
        pass
    else:
        print "UNHANDLED environ_cb", cmd
        pass
    return False


@CFUNCTYPE(None)
def poll_cb():
    pass


@CFUNCTYPE(c_short, c_uint, c_uint, c_uint, c_uint)
def input_cb(port, device, index, id):
    return 0  # not pressed

last_framebuffer = None


@CFUNCTYPE(None, c_void_p, c_uint, c_uint, c_size_t)
def video_cb(data, width, height, pitch):
    print "video_cb", data, width, height, pitch
    pixels = cast(data, POINTER(c_ushort*512*1024))

    global last_framebuffer
    last_framebuffer = pixels.contents


@CFUNCTYPE(c_size_t, c_void_p, c_size_t)
def audio_batch_cb(data, frames):
    print "audio_batch_cb", frames
    samples = cast(data, POINTER(c_ushort))
    print "a sample:", samples[100]
    return 0  # ignored in snes9x_next core

# LOAD THE DYNAMIC LIBRARY
core = cdll.LoadLibrary(CORE_LIBRARY_PATH)

# API VERSION
assert core.retro_api_version() == 1

# SYSTEM INFO
system_info = retro_system_info()
core.retro_get_system_info(byref(system_info))
print "SYSTEM INFO"
print "library_name:", system_info.library_name
print "library_version:", system_info.library_version
print "valid_extensions:", system_info.valid_extensions
print "need_fullpath?", system_info.need_fullpath
print "block_extract?", system_info.block_extract


# AV INFO
av_info = retro_system_av_info()
core.retro_get_system_av_info(byref(av_info))
print "AV INFO"
print "base_width:", av_info.geometry.base_width
print "base_height:", av_info.geometry.base_height
print "max_width:", av_info.geometry.max_width
print "max_height:", av_info.geometry.max_height
print "aspect_ratio:", av_info.geometry.aspect_ratio
print "fps:", av_info.timing.fps
print "sample_rate:", av_info.timing.sample_rate


# REGISTER CALLBACKS (so far, each of these seems to be required)
core.retro_set_environment(environ_cb)
core.retro_set_input_poll(poll_cb)
core.retro_set_input_state(input_cb)
core.retro_set_video_refresh(video_cb)
core.retro_set_audio_sample_batch(audio_batch_cb)

# INIT

core.retro_init()

# LOAD GAME
byte_count = os.path.getsize(ROM_PATH)
rom_bytes = (c_byte * byte_count)()
with open(ROM_PATH, "r") as f:
    rom_data = f.readinto(rom_bytes)

game = retro_game_info()
game.path = ROM_PATH
game.data = cast(byref(rom_bytes), c_void_p)
game.size = byte_count
game.meta = None

core.retro_load_game.restype = c_bool
game_loaded = core.retro_load_game(byref(game))
print "game loaded?", game_loaded


# SERIALIZATION (not used for now)

core.retro_serialize_size.restype = c_size_t
serialize_size = core.retro_serialize_size()
print "retro_serialize_size:", serialize_size

core.retro_serialize.argtypes = [c_void_p, c_size_t]
core.retro_serialize.restype = c_bool

# MAIN LOOP

simulation_done = False
step = 0


# control the main loop via a signal handler because interrupt might occur
# when we aren't in a Python context to capture it as an exception
def interrupt(sig, frame):
    global simulation_done
    simulation_done = True

signal.signal(signal.SIGINT, interrupt)

serialize_buffer = (c_char*serialize_size)()

while not simulation_done:
    print ""
    print "step:", step
    core.retro_run()
    step += 1

    if step >= 3000 and step % 5 == 0:
        arr = np.frombuffer(
            last_framebuffer,
            dtype=np.uint16,
            count=512*1024
        ).reshape((512, 1024))[0:224, 0:256].astype(np.uint32)
        screen = np.zeros((224, 256, 3), dtype=np.uint8)
        screen[:, :, 0] = (arr & 0xF800) >> 8
        screen[:, :, 1] = (arr & 0x07E0) >> 3
        screen[:, :, 2] = (arr & 0x001F) << 3
        # plt.subplot(211)
        # plt.imshow(screen, hold=False)

        core.retro_serialize(byref(serialize_buffer), serialize_size)

        # plt.subplot(212)
        # s = 68478+11
        # plt.imshow(
        #    np.frombuffer(serialize_buffer,dtype=np.uint8)[s:s+(1<<16)].reshape((-1,4,4,8,8,8)).swapaxes(1,2).swapaxes(2,3).swapaxes(2,4).reshape(-1,4*64),
        #    interpolation='nearest',
        #    hold=False)
        # plt.imshow(
        #     np.frombuffer(serialize_buffer,
        #                   dtype='>u2')[20000:26400].reshape(-1, 32),
        #     interpolation='nearest',
        #     hold=False)
        # plt.pause(0.01)

np.save("last_serialized.npy", np.frombuffer(serialize_buffer, dtype=np.uint8))

print "SIMULATION STOPPED"

core.retro_unload_game()
core.retro_deinit()

# PLAYING WITH LIBRETRO FROM PYTHON
# Can I just build a dumb video in memory???

import sys
import os
# import signal
from Queue import Queue

# visualization
# import matplotlib.pyplot as plt
# import numpy as np

# We'll use ctypes to access the libretro C API exposed by the
# snes9x_next core
from ctypes import (CFUNCTYPE,
                    POINTER,
                    Structure,
                    byref,
                    c_bool,
                    c_byte,
                    # c_char,
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

video_q = Queue()
environ_q = Queue()

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

config = {}


# Python functions wrapped as C function pointers
@CFUNCTYPE(c_bool, c_uint, c_void_p)
def environ_cb(cmd, data):
    global environ_q
    config = {}
    if cmd == RETRO_ENVIRONMENT_GET_OVERSCAN:
        pass
    elif cmd == RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL:
        level = cast(data, POINTER(c_uint)).contents.value
        config['performance_level'] = level
        assert level == 7
    elif cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
        pixel_format = cast(data, POINTER(c_int)).contents.value
        config['pixel_format'] = pixel_format
        assert pixel_format == RETRO_PIXEL_FORMAT_RGB565
        # return True  # Why did we return here?
    elif cmd == RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
        descriptors = cast(data, POINTER(retro_input_descriptor))
        found = []
        i = 0
        while descriptors[i].description:
            d = descriptors[i]
            found.append({
                'port': d.port,
                'device': d.device,
                'index': d.index,
                'id': d.id,
                'description': d.description,
                })
            i += 1
        # config['input_descriptors'] = found
    elif cmd == RETRO_ENVIRONMENT_SET_VARIABLES:
        variables = cast(data, POINTER(retro_variable))
        i = 0
        found = {}
        while variables[i].key:
            variable = variables[i]
            found[variable.key] = variable.value
            i += 1
        config['variables'] = found
    elif cmd == RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        pass
    elif cmd == RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
        pass
    elif cmd == RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
        pass
    elif cmd == RETRO_ENVIRONMENT_SET_SUPPORT_ACHIEVEMENTS:
        pass
    else:
        # print "UNHANDLED environ_cb", cmd
        pass
    environ_q.put(config)
    return False


@CFUNCTYPE(None)
def poll_cb():
    pass


@CFUNCTYPE(c_short, c_uint, c_uint, c_uint, c_uint)
def input_cb(port, device, index, id):
    return 0  # not pressed


@CFUNCTYPE(None, c_void_p, c_uint, c_uint, c_size_t)
def video_cb(data, width, height, pitch):
    # print "video_cb", data, width, height, pitch
    pixels = cast(data, POINTER(c_ushort*512*1024))

    global video_q
    video_q.put(pixels.contents)


@CFUNCTYPE(c_size_t, c_void_p, c_size_t)
def audio_batch_cb(data, frames):
    # print "audio_batch_cb", frames
    # samples = cast(data, POINTER(c_ushort))
    # print "a sample:", samples[100]
    return 0  # ignored in snes9x_next core


class Emulator:
    def __init__(self, libretro_core_library_path):
        # LOAD THE DYNAMIC LIBRARY
        self.core = cdll.LoadLibrary(libretro_core_library_path)

        # API VERSION
        assert self.core.retro_api_version() == 1

        # SYSTEM INFO
        system_info = retro_system_info()
        self.core.retro_get_system_info(byref(system_info))
        self.config = {}
        self.config['system_info'] = {
            "library_name": system_info.library_name,
            "library_version": system_info.library_version,
            "valid_extensions": system_info.valid_extensions,
            "need_fullpath?": system_info.need_fullpath,
            "block_extract?": system_info.block_extract,
        }

        # AV INFO
        av_info = retro_system_av_info()
        self.core.retro_get_system_av_info(byref(av_info))
        self.config['av_info'] = {
            "base_width": av_info.geometry.base_width,
            "base_height": av_info.geometry.base_height,
            "max_width": av_info.geometry.max_width,
            "max_height": av_info.geometry.max_height,
            "aspect_ratio": av_info.geometry.aspect_ratio,
            "fps": av_info.timing.fps,
            "sample_rate": av_info.timing.sample_rate,
        }

        # REGISTER CALLBACKS (so far, each of these seems to be required)
        self.core.retro_set_environment(environ_cb)
        self.core.retro_set_input_poll(poll_cb)
        self.core.retro_set_input_state(input_cb)
        self.core.retro_set_video_refresh(video_cb)
        self.core.retro_set_audio_sample_batch(audio_batch_cb)

        # INIT
        self.core.retro_init()

        self.game = None

    def load_game(self, rom_path):
        # LOAD GAME
        byte_count = os.path.getsize(rom_path)
        rom_bytes = (c_byte * byte_count)()
        with open(rom_path, "r") as f:
            f.readinto(rom_bytes)

        self.game = retro_game_info()
        self.game.path = rom_path
        self.game.data = cast(byref(rom_bytes), c_void_p)
        self.game.size = byte_count
        self.game.meta = None

        self.core.retro_load_game.restype = c_bool
        game_loaded = self.core.retro_load_game(byref(self.game))
        print "game loaded?", game_loaded

        # SERIALIZATION (not used for now)
        # self.core.retro_serialize_size.restype = c_size_t
        # serialize_size = core.retro_serialize_size()
        # # print "retro_serialize_size:", serialize_size
        # self.core.retro_serialize.argtypes = [c_void_p, c_size_t]
        # self.core.retro_serialize.restype = c_bool

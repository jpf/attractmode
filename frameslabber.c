#include <assert.h>
#include <libretro.h>
#include <stdio.h>
#include <stdlib.h>

FILE* slab_file = NULL;

bool environ_cb(unsigned int cmd, void* data) {
	//printf("environ_cb %u, %p\n", cmd, data);
	switch(cmd) {
		case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
			{
				unsigned int format = *((unsigned int*)data);
				assert(format == RETRO_PIXEL_FORMAT_RGB565);
			}
			return true;
		default:
			return false;

	}
}

void poll_cb() {
	//printf("poll_cb\n");
}

short input_cb(unsigned int port, unsigned int device, unsigned int index, unsigned int id) {
	//printf("input_cb %u, %u, %u, %u\n", port, device, index, id);
	return 0; // not pressed
}

void video_cb(const void* data, unsigned int width, unsigned int height, size_t pitch) {
	// printf("video_cb %p, %u, %u, %zu\n", data, width, height, pitch);

	FILE* file = slab_file;
	for(int row=0; row < height; row++) {
		fwrite(data, 2, width, file);
		data += pitch;
	}

}

size_t audio_batch_cb(const short* data, size_t frames) {
	//printf("audio_batch_cb %p, %zu\n", data, frames);
	return 0;
}

int main(int argc, char* argv[]) {

	if (argc != 4) {
		fprintf(stderr, "usage: %s rom_path slab_path num_frames\n", argv[0]);
		return 1;
	}

 
	const char* rom_path = argv[1];
	const char* slab_path = argv[2];
	int total_frame_count;
  	sscanf(argv[3], "%d", &total_frame_count);

	assert(retro_api_version() == 1);

	struct retro_system_info system_info;
	retro_get_system_info(&system_info);
	printf("library_name: %s\n", system_info.library_name);
	printf("library_version: %s\n", system_info.library_version);

	struct retro_system_av_info system_av_info;
	retro_get_system_av_info(&system_av_info);
	printf("base_width: %u\n", system_av_info.geometry.base_width);
	printf("base_height: %u\n", system_av_info.geometry.base_height);
	printf("aspect_ratio: %f\n", system_av_info.geometry.aspect_ratio);
	printf("fps: %f\n", system_av_info.timing.fps);
	printf("sample_rate: %f\n", system_av_info.timing.sample_rate);

	retro_set_environment(&environ_cb);
	retro_set_input_poll(&poll_cb);
	retro_set_input_state(&input_cb);
	retro_set_video_refresh(&video_cb);
	retro_set_audio_sample_batch(&audio_batch_cb);

	retro_init();

	FILE* rom_file = fopen(rom_path, "rb");
	fseek(rom_file, 0L, SEEK_END);
	size_t rom_bytes = ftell(rom_file);
	fseek(rom_file, 0L, SEEK_SET);

	void* rom_data = malloc(rom_bytes);
	fread(rom_data, 1, rom_bytes, rom_file);
	fclose(rom_file);

	struct retro_game_info game_info;
	game_info.path = rom_path;
	game_info.data = rom_data;
	game_info.size = rom_bytes;
	game_info.meta = NULL;

	retro_load_game(&game_info);
	

	slab_file = fopen(slab_path, "wb");

	for(int frame = 0; frame < total_frame_count; frame++) {
		//printf("frame %d\n", frame);
		retro_run();
	}

	fclose(slab_file);
	slab_file = NULL;

	retro_unload_game();

	free(rom_data);

	retro_deinit();

	return 0;
}

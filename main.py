from load_frames import *
from calibration import *
from astrometry_connection import * 

def load():
    lights = load_light_frames(directory, light_frame_indicator)
    flats = load_flat_frames(directory, flat_frame_indicator)
    biases = load_bias_frames(directory, bias_frame_indicator)
    print('total lights loaded: {0}'.format(len(lights)))
    print('total flats loaded: {0}'.format(len(flats)))
    print('total biases loaded: {0}'.format(len(biases)))

def calibrate():
    flat_pixel_array_list = fits_to_array(flats)
    bias_pixel_array_list = fits_to_array(biases)
    lights_pixel_array_list = fits_to_array(lights)
    master_flat_pixel_array = median_flats(flat_pixel_array_list, bias_pixel_array_list, len(flats), len(biases), directory, new_directory)
    master_bias_pixel_array = median_biases(bias_pixel_array_list, len(biases), directory, new_directory)
    #in case we want to see master composite calibration frames
    plt.show()

def solve():
    plate_solve_frame_list(paths)

if __name__ == "__main__":
    load()
    calibrate()
    solve()
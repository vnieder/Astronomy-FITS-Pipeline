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

def calibrate(dir, transit_name):
    master_flat, master_bias = create_master_frames(dir)
    calibrate_light_frames(dir, transit_name, master_flat, master_bias)
    #in case we want to see master composite calibration frames
    plt.show()

def solve():
    plate_solve_frame_list(paths)

if __name__ == "__main__":
    dir = '/Users/spencerfreeman/Desktop/stepUp/2024-09-4-skuban'
    transit_name = 'qatar-5b'
    load()
    calibrate(dir, transit_name)
    solve()
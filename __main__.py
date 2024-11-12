from calibration import create_master_frames, calibrate_light_frames
from astrometry_connection import * 
import matplotlib.pyplot as plt
from astropy.io import fits

def calibrate(dir, transit_name):
    master_flat, master_bias = create_master_frames(dir)
    lights_calibrated = calibrate_light_frames(dir, transit_name, master_flat, master_bias)
    #in case we want to see master composite calibration frames
    return lights_calibrated

def solve():
    plate_solve_frame_list(paths)

if __name__ == "__main__":
    dir = '/Users/spencerfreeman/Desktop/stepUp/2024-09-4-skuban'
    transit_name = 'qatar-5b'
    lights_calibrated = calibrate(dir, transit_name)
    hdulist = lights_calibrated[0].to_hdu()
    plt.imshow(hdulist[0].data)
    plt.show()
    
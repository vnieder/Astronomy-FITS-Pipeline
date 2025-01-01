from calibration import create_master_frames, calibrate_light_frames
from photometry import perform_photometry, plot
import matplotlib.pyplot as plt
import numpy as np

def calibrate(dir:str, transit_name:str, wcs:list, flip:bool) -> list:
    master_flat, master_bias = create_master_frames(dir, flip)
    lights_calibrated = calibrate_light_frames(dir, transit_name, master_flat, master_bias, wcs, flip)
    #in case we want to see master composite calibration frames
    return lights_calibrated

def read_config_file(config_file_path:str) -> dict:
    config = {}
    with open(config_file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if ": " in line:
                key, value = line.split(": ", 1)
                config[key] = value
    return config
    
if __name__ == "__main__":
    config_file_path = input("Enter path to config file: ")
    config_dict = read_config_file(config_file_path)
    
    dir = config_dict["Main Directory (ex. /Users/spencerfreeman/Desktop/pipeline_test)"]
    transit_name = config_dict["Target Name"]
    wcs = config_dict["RA/DEC (ex. 00:28:12.944,+42:03:40.95)"]
    x_targ,y_targ = config_dict["Target Coordinates (pix)"]
    x_comp,y_comp = config_dict["Comparison Coordinates (pix)"]
    x_vali,y_vali = config_dict["Validation Coordinates (pix)"]
    threshold_multiplier = config_dict["Source Detection Threshold"]
    catalogue_indicator = config_dict["Catalogue Indicator"]
    light_frame_indicator = config_dict["Light Frame Indicator"]
    output_dir = config_dict["Output Directory"]
    main_title = config_dict["Main Plot Title (transit name)"]
    date = config_dict["Observation Date (MM/DD/YYYY)"]
    observer_name = config_dict["Observer Name"]
    
    #lights_calibrated is a list of CCDData objects, arrays are accsessd by data attribute.
    lights_calibrated = calibrate(dir, transit_name, wcs, flip=True)
    
    '''
    Perform photometry writes catalogues of all sources in given frames to the specified output directory. These catalogues 
    are then searched for points that minimize the distance to estimation pixel locations. Lists corresponding to target star flux, 
    comparison star flux, and validation star flux are returned and passed to the plot function. 
    '''
    ###photometry###
    target_lc, comparison_lc, validation_lc = perform_photometry(light_frame_indicator, catalogue_indicator, output_dir, threshold_multiplier, 
                                                                 target_location=(x_targ,y_targ), comparison_location=(x_comp,y_comp), validation_location=(x_vali,y_vali))
    
    '''
    The plot function from the photometry.py module generates a plot of relative normalized flux for both target and validation stars.
    The function also generates and saves a csv file of the 
    '''
    ###plotting###
    plot(target_lc, comparison_lc, validation_lc, output_dir, main_title, date, observer_name)
   
    
        
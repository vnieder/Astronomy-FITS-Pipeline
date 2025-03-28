from calibration import create_master_frames, calibrate_light_frames
from photometry import perform_photometry, plot
import ast

def calibrate(dir:str, transit_name:str, wcs:list, flip:bool) -> list:
    master_flat, master_bias = create_master_frames(dir, flip)
    lights_calibrated = calibrate_light_frames(dir, transit_name, master_flat, master_bias, wcs, flip)
    # In case we want to see master composite calibration frames
    return lights_calibrated

def read_config_file(config_file_path:str) -> dict:
    config = {}
    with open(config_file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if "," in line and ": " in line and "RA/DEC" not in line:
                key, value = line.split(": ", 1)
                value = ast.literal_eval(value)
                config[key] = value
            elif ": " in line:
                key, value = line.split(": ", 1)
                config[key] = value
    return config
    
if __name__ == "__main__":
    config_file_path = input("Enter full path of config.txt file: ")  # e.g. "/path/to/config.txt"
    config_dict = read_config_file(config_file_path)
    
    dir = config_dict["Main Directory (ex. /Users/spencermfreeman/Desktop/pipeline_test)"]
    transit_name = config_dict["Target Name"]
    wcs = config_dict["RA/DEC (ex. 00:28:12.944,+42:03:40.95)"]
    # Target radius doubles as the aperture number
    target_radius = int(config_dict["Target Radius"]) 
    x_targ, y_targ = tuple(config_dict["Target Coordinates (pix)"])
    x_comp, y_comp = tuple(config_dict["Comparison Coordinates (pix)"])
    x_vali, y_vali = tuple(config_dict["Validation Coordinates (pix)"])
    threshold_multiplier = int(config_dict["Source Detection Threshold"])
    catalogue_indicator = config_dict["Catalogue Indicator"]
    light_frame_indicator = config_dict["Light Frame Indicator"]
    output_dir = config_dict["Output Directory"]
    main_title = config_dict["Main Plot Title (transit name)"]
    date = config_dict["Observation Date (MM/DD/YYYY)"]
    observer_name = config_dict["Observer Name"]
    iaper = target_radius
    
    # lights_calibrated is a list of CCDData objects, arrays accessed via the data attribute.
    lights_calibrated = calibrate(dir, transit_name, wcs, flip=True)
    
    '''
    Perform photometry writes catalogues of all sources in given frames to the specified output directory.
    These catalogues are then searched for points that minimize the distance to estimation pixel locations.
    Lists corresponding to target star flux, comparison star flux, and validation star flux are returned and passed to the plot function. 
    '''
    ### Photometry ###
    target_lc, comparison_lc, validation_lc = perform_photometry(light_frame_indicator, catalogue_indicator, output_dir, threshold_multiplier, target_radius,
                                                                 target_location=(x_targ, y_targ), comparison_location=(x_comp, y_comp), validation_location=(x_vali, y_vali))
    
    '''
    The plot function from the photometry.py module generates a plot of relative normalized flux for both target and validation stars.
    It also generates and saves a CSV file.
    '''
    ### Plotting ###
    plot(target_lc, comparison_lc, validation_lc, iaper, output_dir, main_title, date, observer_name)
    
from astroquery.astrometry_net import AstrometryNet

# This is a very simple way to access the Astrometry.net plate solving API.
# (Additional instructions on configuration are in the file documentation.)
# User-defined example filepaths for WCS solving:
filepath = '/Users/spencerfreeman/Desktop/stepUp/freeman2024-09-03/WASP-135b-0001_lrp.fit'
filepath1 = '/Users/spencerfreeman/Desktop/stepUp/freeman2024-09-03/WASP-135b-0002_lrp.fit'
filepath2 = '/Users/spencerfreeman/Desktop/stepUp/freeman2024-09-03/WASP-135b-0003_lrp.fit'

paths = [filepath, filepath1, filepath2]

ast = AstrometryNet()
header_list = []

def plate_solve_frame_list(paths):
    for path in paths:
        solve_for_wcs(path)
    return len(header_list)

def solve_for_wcs(file_path):
    wcs_header = ast.solve_from_image(file_path, force_image_upload=True)
    header_list.append(wcs_header)
    print(wcs_header)
    return wcs_header

if __name__ == "__main__":
    solve_for_wcs(filepath)
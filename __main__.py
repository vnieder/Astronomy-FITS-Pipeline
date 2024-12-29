from calibration import create_master_frames, calibrate_light_frames
from photometry import perform_photometry, plot
import matplotlib.pyplot as plt
import numpy as np

def calibrate(dir:str, transit_name:str) -> list[CCDdata]:
    master_flat, master_bias = create_master_frames(dir)
    lights_calibrated = calibrate_light_frames(dir, transit_name, master_flat, master_bias)
    #in case we want to see master composite calibration frames
    return lights_calibrated
    
if __name__ == "__main__":
    dir = '/Users/spencerfreeman/Desktop/stepUp/2024-09-4-skuban'
    transit_name = 'qatar-5b'
    #lights_calibrated is a list of CCDData objects, arrays are accsessd by data attribute.
    lights_calibrated = calibrate(dir, transit_name)
    
    print(lights_calibrated)
    
    '''
    Perform photometry writes catalogues of all sources in given frames to the specified output directory. These catalogues 
    are then searched for points that minimize the distance to estimation pixel locations. Lists corresponding to target star flux, 
    comparison star flux, and validation star flux are returned and passed to the plot function. 
    '''
    ###photometry###
    x_targ,y_targ = (2403.662364756954, 2018.2046627353204)
    x_comp,y_comp = (1756.1089736736467, 2364.1375110432928)
    x_vali,y_vali = (1988.9627767690627, 1765.0694999895554)
    threshold_multiplier = 15.
    catalogue_indicator = "cat"
    light_frame_indicator = "lrp"
    output_dir = '/Users/spencerfreeman/Desktop/PersonalCS/CurrentPipeline/test_input/test_output'
    target_lc, comparison_lc, validation_lc = perform_photometry(light_frame_indicator, catalogue_indicator, output_dir, threshold_multiplier, 
                                                                 target_location=(x_targ,y_targ), comparison_location=(x_comp,y_comp), validation_location=(x_vali,y_vali))
    
    '''
    The plot function from the photometry.py module generates a plot of relative normalized flux for both target and validation stars.
    The function also generates and saves a csv file of the 
    '''
    ###plotting###
    main_title = "Qatar-5"
    date = "09/05/2024"
    observer_name = "Marina Skuban"
    
    plot(target_lc, comparison_lc, validation_lc, output_dir, main_title, date, observer_name)
   
    
        
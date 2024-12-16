from astropy.stats import mad_std
from astropy import units as u
from astropy.nddata import CCDData
import ccdproc as ccdp
import ccdproc as ccdp
from load_frames import *
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def make_subdir(directory):
    calibrated_data = Path(directory, 'master_frames_test')
    calibrated_data.mkdir(exist_ok=True)
    return calibrated_data

def create_master_frames(directory):
    #we should not need to define another imagecollection
    main_path = Path(directory)
    files = ccdp.ImageFileCollection(main_path)
    
    biases = files.files_filtered(imagetyp='Bias Frame', include_path=True)
    flats = files.files_filtered(imagetyp='Flat Field', include_path=True)
    
    calibrated_data = make_subdir(directory)
    
    # Load the bias frames as CCDData with appropriate units
    bias_data = []
    for bias_file in biases:
        # Read each file into a CCDData object with units (e.g., "adu" for analog-to-digital units)
        bias_frame = CCDData.read(bias_file, unit=u.adu)
        bias_data.append(bias_frame)
    
    master_bias = ccdp.combine(bias_data, method='average', sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                                sigma_clip_func=np.ma.median, sigma_clip_dev_func=mad_std, mem_limit=350e6)

    master_bias.meta['combined'] = True
    master_bias.data = master_bias.data.astype('float32')
    master_bias.write(calibrated_data / 'master_bias.fit', overwrite=True)

    '''
    Make the master flat:
    it is assumed that only r' filter is used in observation, if multiple filters were used to create 
    multiple flats, one master flat should be created per filter
    '''
    
    flat_data = []
    for flat_file in flats:
        flat_field = CCDData.read(flat_file, unit=u.adu)
        flat_data.append(flat_field)
            
    master_flat = ccdp.combine(flat_data, method='average', scale=inv_median, sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                                sigma_clip_func=np.ma.median, signma_clip_dev_func=mad_std, mem_limit=350e6)

    master_flat.meta['combined'] = True
    master_flat.data = master_flat.data.astype('float32')
    master_flat.write(calibrated_data / 'master_flat.fit', overwrite = True)
    
    #delete statements likely assist in the memory overflow errors
    del files
    return master_bias, master_flat

#used in the stats associated with the flat field combination process, see arguments of ccdp.combine() function
def inv_median(a):
    return 1 / np.median(a)
    
def calibrate_light_frames(directory, transit_name, master_bias, master_flat):
    main_path = Path(directory)
    files = ccdp.ImageFileCollection(main_path)
    transit_name = transit_name
    #obtain all of the light frames
    lights = files.files_filtered(imagetyp='Light Frame', include_path=True)

    #process each light frame in a compact manner and add to list, might need to add a list of the processed lights, removed to save on space.
    counter=1
    light_frames = []
    for light in lights:
        light_frame = CCDData.read(light, unit=u.adu)
        reduced = ccdp.ccd_process(light_frame, master_bias=master_bias, master_flat=master_flat)
        reduced.data = reduced.data.astype('float32')
        light_frames.append(reduced)
        reduced.write('{0}/test_output/{1}_lrp_out_{2}.fit'.format(directory, transit_name, counter), overwrite=True)
        counter+=1
        
    del files
    return light_frames
    
if __name__ == "__main__":
    #writes the master flat and master bias to the subdirectory using newer method
    #form of path may be important as of now, this should not matter.
    dir_input = '/Users/spencerfreeman/Desktop/PersonalCS/CurrentPipeline/test_input'
    transit_name = 'qatar-5b'
    master_flat, master_bias = create_master_frames(dir_input)
    calibrate_light_frames(dir_input, transit_name, master_flat, master_bias)
    
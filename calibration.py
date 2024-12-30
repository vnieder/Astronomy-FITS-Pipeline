from astropy.stats import mad_std
from astropy import units as u
from astropy.nddata import CCDData
import ccdproc as ccdp
import ccdproc as ccdp
from load_frames import *
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from astropy.coordinates import SkyCoord
import glob
from astropy.io import fits

def make_subdir(directory):
    calibrated_data = Path(directory, 'master_frames_test')
    calibrated_data.mkdir(exist_ok=True)
    return calibrated_data

def create_master_frames(directory, flip:bool):
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
    if(flip):
        master_bias.data = np.flipud(master_bias.data)
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
    if(flip):
        master_flat.data = np.flipud(master_flat.data)
    master_flat.data = master_flat.data.astype('float32')
    master_flat.write(calibrated_data / 'master_flat.fit', overwrite = True)
    
    #delete statements likely assist in the memory overflow errors
    del files
    return master_bias, master_flat

#used in the stats associated with the flat field combination process, see arguments of ccdp.combine() function
def inv_median(a) -> int:
    return 1 / np.median(a)
    
def calibrate_light_frames(directory:str, transit_name:str, master_bias:CCDData, master_flat:CCDData, target_coords_wcs:list, flip:bool) -> list:
    main_path = Path(directory)
    files = ccdp.ImageFileCollection(main_path)
    
    FOCALLEN = 3962.3999023437500 #mm
    PIXELSIZE = 9 #um
    pixscale=206.265*(PIXELSIZE/FOCALLEN)
    
    c=SkyCoord(target_coords_wcs[0],target_coords_wcs[1],frame='icrs',unit=(u.hourangle,u.degree))
    ra=c.ra.degree; dec=c.dec.degree
    
    gain, readout_noise = get_gain_readout_noise(directory, "bias", "frp")
    
    #obtain all of the light frames
    lights = files.files_filtered(imagetyp='Light Frame', include_path=True)
    #process each light frame in a compact manner and add to list, might need to add a list of the processed lights, removed to save on space.
    counter=1
    light_frames = []
    for light in lights:
        print(f"Reducing light frames, flat fielding, debiasing, flipping : {counter}/{len(lights)}")
        light_frame = CCDData.read(light, unit=u.adu)
        reduced = ccdp.ccd_process(light_frame, master_bias=master_bias, master_flat=master_flat)
        edit_header(reduced, ra, dec, pixscale, gain, readout_noise)
        #flip the data array such that north is up if deemed neccessary
        
        if(flip):
            reduced.data = np.flipud(reduced.data)
        #compress to single precision image
        reduced.data = reduced.data.astype('float32')
        light_frames.append(reduced)
        #write to the output directory, lets assume north is up and add functionality if neccessary.
        reduced.write('{0}/test_output/{1}_lrp_out_{2}.fit'.format(directory, transit_name, counter), overwrite=True)
        counter+=1
    del files
    return light_frames

def edit_header(reduced, ra, dec, pixscale, gain, readout_noise):
    reduced.meta['epoch']=2000.0
    reduced.meta['CRVAL1']=ra
    reduced.meta['CRVAL2']=dec
    reduced.meta['CRPIX1']=reduced.meta['NAXIS1']/2.0
    reduced.meta['CRPIX2']=reduced.meta['NAXIS2']/2.0
    reduced.meta['CDELT1']=-pixscale/3600.0 # minus for left east
    reduced.meta['CDELT2']=pixscale/3600.0
    reduced.meta['CTYPE1']='RA---TAN' # projection type
    reduced.meta['CTYPE2']='DEC--TAN'
    reduced.meta['GAIN']=(gain,'GAIN in e-/ADU')
    reduced.meta['RDNOISE']=(readout_noise,'readout noise in electron')

def get_gain_readout_noise(directory:str, bias_indicator:str, flat_indicator:str) -> tuple:
    bias_list = glob.glob(directory + f"/*{bias_indicator}*")
    flat_list = glob.glob(directory + f"/*{flat_indicator}*")
    print(len(bias_list))
    print(len(flat_list))
    bias_data = []
    flat_data = []
    
    for bias_file in bias_list:
        data = fits.getdata(bias_file)[1500-256:1500+256,1500-256:1500+256]
        bias_data.append(data)
    for flat_file in flat_list:
        data = fits.getdata(flat_file)[1500-256:1500+256,1500-256:1500+256]
        flat_data.append(data)
    
    bias_combined = np.median(bias_data, axis=0)
    flat_combined = np.median(flat_data, axis=0)
    
    # Calculate gain and read noise
    mean_flat = np.mean(flat_combined)
    mean_bias = np.mean(bias_combined)
    std_flat = np.std(flat_combined)
    std_bias = np.std(bias_combined)

    gain = (mean_flat - mean_bias) / (std_flat**2 - std_bias**2)
    readnoise = gain * std_bias / np.sqrt(2)  
      
    print(f"gain: {gain}, readoout: {readnoise}")
    return (gain, readnoise)

if __name__ == "__main__":
    #writes the master flat and master bias to the subdirectory using newer method
    #form of path may be important as of now, this should not matter.
    dir_input = '/Users/spencerfreeman/Desktop/PersonalCS/CurrentPipeline/test_input/'
    transit_name = 'qatar-5b'
    target_coords_wcs = ["00:28:12.944", "+42:03:40.95"]
    master_flat, master_bias = create_master_frames(dir_input, True)
    
    plt.imshow(master_bias.data)
    plt.show()
    calibrate_light_frames(dir_input, transit_name, master_flat, master_bias, target_coords_wcs, True)
    
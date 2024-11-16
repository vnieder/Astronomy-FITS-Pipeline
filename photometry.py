import numpy as np
from astropy.stats import sigma_clipped_stats
from astropy.io import fits
import matplotlib.pyplot as plt
from astropy.nddata import Cutout2D
from astropy import units as u
import matplotlib.pyplot as plt
from astropy.visualization import SqrtStretch
from astropy.visualization.mpl_normalize import ImageNormalize
from astropy.stats import SigmaClip
from photutils.background import Background2D, MedianBackground
from photutils.detection import DAOStarFinder
from photutils.aperture import CircularAperture
from photutils.centroids import centroid_quadratic
from photutils.profiles import RadialProfile
from photutils.profiles import CurveOfGrowth
from astropy.stats import mad_std
from astropy import units as u
from astropy.nddata import CCDData
import ccdproc as ccdp
import ccdproc as ccdp
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

'''We are currently passing rough estimates of pixel location and lining up with the best match on the chart provided by DAO'''

def example_load(path):
    main_path = Path(path)
    files = ccdp.ImageFileCollection(main_path)
    lights = files.files_filtered(imagetyp='Light Frame', include_path=True)
    return lights

def get_flux(light_frame_CCDData, x_pix_est, y_pix_est):
    #we must accsess the array with .data property of light_frame
    light_frame = CCDData.read(light_frame_CCDData, unit=u.adu)
    light_arr = light_frame.data
    
    position = (x_pix_est, y_pix_est)
    size = (500, 500)# pixels subject to change.
    cutout = Cutout2D(light_arr, position, size)
    
    sigma_clip = SigmaClip(sigma=3.0)
    bkg_estimator = MedianBackground()
    bkg = Background2D(cutout.data, (50, 50), filter_size=(3, 3), sigma_clip=sigma_clip, bkg_estimator=bkg_estimator)
    cutout.data = cutout.data-bkg.background #subtract background from cutout data
    
    return

#returns the best coordinates to use based on the given guess and the objects present. 
def match_with_table_entry(light_frame_CCDdata, x_pix_est, y_pix_est):
    x = x_pix_est
    y = y_pix_est
    return [x,y]

#we will be passing a CCDData object
def perform_photometry(light_frames):
    
    target_x_est = 278.62    
    target_y_est = 317.35
    
    #TODO: get comp estimates,eventually user input. 
    comp_x_est = 1000
    comp_y_est = 1000
    
    target_flux_values = []
    comparison_flux_values = []
    
    for i,light_frame_CCDData in enumerate(light_frames):
        
        flux_tar = get_flux(light_frame_CCDData, target_x_est, target_y_est)
        flux_comp = get_flux(light_frame_CCDData, comp_x_est, comp_y_est)
        
        target_flux_values.append(flux_tar)
        comparison_flux_values.append(flux_comp)
        
    return target_flux_values, comparison_flux_values

if __name__ == "__main__":
    lights = example_load('/Users/spencerfreeman/Desktop/stepUp/2024-09-4-skuban/example1-reduced/test')
    perform_photometry(lights)
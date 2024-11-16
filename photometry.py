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

'''We are currently passing rough estimates of pixel location and lining up with the best match on the chart provided by DAO'''

def get_flux_target(light_frame_CCDData):
    
    return 

def get_flux_comparison(light_frame_CCDData):
     
    return

#we will be passing a CCDData object
def perform_photometry(light_frames):
    
    target_flux_values = []
    comparison_flux_values = []
    
    for i,light_frame_CCDData in enumerate(light_frames):
        
        flux_tar = get_flux_target(light_frame_CCDData)
        flux_comp = get_flux_comparison(light_frame_CCDData)
        
        target_flux_values.append(flux_tar)
        comparison_flux_values.append(flux_comp)
        
    return target_flux_values, comparison_flux_values


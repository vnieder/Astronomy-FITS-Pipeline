import numpy as np
from astropy.stats import sigma_clipped_stats
import matplotlib.pyplot as plt
from astropy.nddata import Cutout2D
from astropy import units as u
import matplotlib.pyplot as plt
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

def get_flux(light_frame, x_pix_est, y_pix_est, target_name, size_cutout, position_cutout):
    #we must accsess the array with .data property of light_frame
    light_arr = light_frame.data
    
    position = position_cutout
    size = size_cutout # pixels subject to change
    cutout = Cutout2D(light_arr, position, size)
    
    sigma_clip = SigmaClip(sigma=3.0)
    bkg_estimator = MedianBackground()
    
    #we need to be sure cutout is in the actual frame, also deal with the (50,50) tuple.
    bkg = Background2D(cutout.data, (50, 50), filter_size=(3, 3), sigma_clip=sigma_clip, bkg_estimator=bkg_estimator)
    cutout.data = cutout.data-bkg.background #subtract background from cutout data
    sources = get_sources(cutout.data)
    x_objective, y_objective = closest_value(sources['xcentroid'], sources['ycentroid'], 252, 327)
    xycen = centroid_quadratic(cutout.data, xpeak=x_objective, ypeak=y_objective)
    
    #get the radial profile, this array might need to be larger
    edge_radii = np.arange(25)
    rp = RadialProfile(cutout.data, xycen, edge_radii, mask=None)
    plot_and_save(rp, "Seeing Profile", target_name, "sp")
    print(x_objective)
    print(y_objective)
    sources.pprint()
    
    flux_array = return_flux_array(cutout.data, xycen, target_name)
    total_flux = sum(flux_array[0:5])
    return total_flux

def return_flux_array(cutout_data, xycen, target_name):
    radii = np.arange(1, 26)
    cog = CurveOfGrowth(cutout_data, xycen, radii, mask=None)
    flux_arr = cog.profile
    plot_and_save(cog, "Curve of Growth", target_name, "cog")
    return flux_arr
    
def plot_and_save(obj, title, star_label, diff):
    obj.plot(label='Radial Profile')
    plt.title("{0} {1}".format(title, star_label))
    plt.savefig('/Users/spencerfreeman/Desktop/stepUp/2024-09-4-skuban/example1-reduced/{0}'.format(diff))

def get_sources(cutout_data):
    mean, median, std = sigma_clipped_stats(cutout_data, sigma=3.0)  
    daofind = DAOStarFinder(fwhm=3.0, threshold=5.*std)  
    sources = daofind(cutout_data - median)  
    for col in sources.colnames:  
        if col not in ('id', 'npix'):
            sources[col].info.format = '%.2f'  # for consistent table output
    return sources

def closest_value(x_centoroids, y_centroids, x_pix_est, y_pix_est):
    x = min(x_centoroids, key=lambda x: abs(x - x_pix_est))
    y = min(y_centroids, key=lambda x: abs(x - y_pix_est))
    return x, y

def get_pixel_location(x_centoroids, y_centroids, x_pix_est, y_pix_est):
    closest_x = x_pix_est
    closest_y = y_pix_est
    x_tolerance = 1
    y_tolerance = 10

    for i,x_loc in enumerate(x_centoroids):
        difference = np.abs(x_loc - closest_x)
        if difference < x_tolerance:
            x_tolerance = difference
            closest_x = x_loc
            closest_y = y_centroids[i]
    
    if closest_x != x_pix_est:
        return closest_x, closest_y
    else:
        print("WARNING: pixel estimate was not satisfactory.")
        return x_pix_est, y_pix_est

#we will be passing a CCDData object
def perform_photometry(light_frames):
    #TODO: these values must not cause errors if the cutout region is changed.
    target_x_est = 252.03    
    target_y_est = 327.26
    
    #TODO: get comp estimates,eventually user input. 
    comp_x_est = 1000
    comp_y_est = 1000
    
    target_flux_values = []
    comparison_flux_values = []
    time = []
    for i,light_frame_CCDData in enumerate(light_frames):
        light_frame = CCDData.read(light_frame_CCDData, unit=u.adu)
        flux_tar = get_flux(light_frame, target_x_est, target_y_est, "Target", (500, 500), (2400, 2000))
        #TODO get better etsimates for comp star
        #flux_comp = get_flux(light_frame_CCDData, comp_x_est, comp_y_est, "Comparison", (500, 500))
        target_flux_values.append(flux_tar)
        #comparison_flux_values.append(flux_comp)
        time.append(light_frame.header['DATE-OBS'])
        
    return target_flux_values, comparison_flux_values, time

if __name__ == "__main__":
    lights = example_load('/Users/spencerfreeman/Desktop/stepUp/2024-09-4-skuban/example1-reduced/test')
    tar_flux_arr, comp_flux_arr, time = perform_photometry(lights)
    fig, ax = plt.subplots()
    ax.scatter(time, tar_flux_arr)
    plt.show()
    

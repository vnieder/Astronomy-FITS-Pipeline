from astropy.stats import sigma_clipped_stats
from astropy.stats import SigmaClip
from photutils.background import Background2D
from photutils.detection import IRAFStarFinder
from photutils.background import SExtractorBackground
from photutils.segmentation import detect_sources
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils.utils import calc_total_error
from photutils.aperture import CircularAperture, aperture_photometry
from astropy.table import Table
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import glob

def background(file:str) -> Background2D:
    data = fits.getdata(file)
    mean, _, std = sigma_clipped_stats(data, sigma=3.0)
    segm = detect_sources(data-mean, 3*std, npixels=5)
    bool_array = segm.data != 0
    sigma_clip = SigmaClip(sigma=3.)
    bkg_estimator = SExtractorBackground()
    bkg = Background2D(data, (64, 64), mask=bool_array,filter_size=(3, 3), sigma_clip=sigma_clip, bkg_estimator=bkg_estimator)
    return bkg

#takes the output files from the data processing steps (located in the output directory) and globs into list, this serves as the input
def write_photometric_catalogues(light_frame_indicator:str, output_dir:str, threshold_multiplier:float) -> None:
    lights_processed=glob.glob(f'{output_dir}/*{light_frame_indicator}*')
    lights_processed.sort()
    radii=[3,4,5,6,8,10,12,15,20,25] ## aperture radii in pixels
    total=len(lights_processed)

    for i,file in enumerate(lights_processed):
        data = fits.getdata(file)
        print(f"Aperture photometry on all objects: file {i+1}/{total}")
        rootname,_ = os.path.splitext(file)
        print(rootname)
        catfile=f'{output_dir}/{i+1}-cat.fits'
        print(file)
        bkg = background(file)
        IRAFfind = IRAFStarFinder(fwhm=3.0, threshold=threshold_multiplier*bkg.background_rms_median,exclude_border=True, sharplo=0.5, sharphi=2.0, roundlo=0.0, roundhi=0.7)
        sources = IRAFfind(data - bkg.background)
        #list of tuples representing position
        positions = [(ix,iy) for ix,iy in zip(sources['xcentroid'],sources['ycentroid'])] 
        #list of apertures, one for each of the radii given (10 total...)
        apertures = [CircularAperture(positions, r=r) for r in radii] 
        gain=0.242759602
        error = calc_total_error(data-bkg.background, bkg.background_rms, gain)
        #aper_phot is a dictionary object of all the sources past the threshold
        aper_phot = aperture_photometry(data - bkg.background, apertures, error=error)
        print(f"Total sources detected: {len(aper_phot)}")
        aper_phot.write(catfile,overwrite=True)
        
def calc_shifts_update_catalogues(output_dir:str) -> None:
    catalogue_files = glob.glob(f'{output_dir}/*cat.fits')
    catalogue_files.sort()
    #initial declarations:
    x1 = []; y1 = [] 
    reference_catalogue = Table.read(catalogue_files[0])
    
    for i,catalogue in enumerate(catalogue_files):
        #upon first iteration, set the reference catalogue to the first entry in the list of cat files
        if i==0:
            reference_catalogue = Table.read(catalogue)
            x1=reference_catalogue['xcenter']
            y1=reference_catalogue['ycenter']
            #add the xshift field if files have not been previously been processed.
            if 'x_shift' not in reference_catalogue.colnames:
                xcol=Table.Column(x1,name='x_shift')
                ycol=Table.Column(y1,name='y_shift')
                reference_catalogue.add_columns([xcol,ycol])
            else:
                reference_catalogue['x_shift']=x1
                reference_catalogue['y_shift']=y1
            reference_catalogue.write(catalogue,overwrite=True)
            print("Initial iteration complete, reference catalogue updated.")        
        else:
            catalogue_of_interest = Table.read(catalogue)
            n_catalogue_OI=len(catalogue_of_interest)
            x2=catalogue_of_interest['xcenter']
            y2=catalogue_of_interest['ycenter']
            XX = []
            YY = [] 
            for j in range(n_catalogue_OI):
                XX.extend((x1-x2[j]))
                YY.extend((y1-y2[j]))
            XX=np.array(XX)
            YY=np.array(YY)
            
            xhist,xbins=np.histogram(XX,range=[-200, 200],bins=400)
            yhist,ybins=np.histogram(YY,range=[-200, 200],bins=400)
            
            #find most common shift values and determine the x/y shift between frames
            idx=np.argmax(xhist)
            xshift_0=(xbins[idx]+xbins[idx+1])/2.0
            idx=np.argmax(yhist)
            yshift_0=(ybins[idx]+ybins[idx+1])/2.0
            print(f"Initial shift X (Iteration {i}): {xshift_0}, Initial Shift Y: {yshift_0}")
            
            #finetune shifts with masking technique
            mask=(np.abs(XX-xshift_0)<3) & (np.abs(YY-yshift_0)<3)
            print("Mask sum: ", mask.sum())
            xshift_finetuned=np.median(XX[mask])
            yshift_finetuned=np.median(YY[mask])
            print(f"Finetuned Shift (Iteration {i}): ", xshift_finetuned, yshift_finetuned)
            
            if 'x_shift' not in catalogue_of_interest.colnames:
                xcol=Table.Column(x2+xshift_finetuned,name='x_shift')
                ycol=Table.Column(y2+yshift_finetuned,name='y_shift')
                catalogue_of_interest.add_columns([xcol,ycol])
            else:
                #add the finetuned xshift to the x and y aperture columns in the catalogue.
                catalogue_of_interest['x_shift']=x2+xshift_finetuned
                catalogue_of_interest['y_shift']=y2+yshift_finetuned
                
            catalogue_of_interest.write(catalogue, overwrite=True)
            
def find_nearest_pair(qtable, x_col:str, y_col:str, target_x:float, target_y:float) -> tuple[float, float]:
    """Finds the (x, y) pair in a QTable that is closest to a given point.
    Args:
        qtable (astropy.table.QTable): The QTable to search.
        x_col (str): The name of the column containing x-coordinates.
        y_col (str): The name of the column containing y-coordinates.
        target_x (float): The x-coordinate of the target point.
        target_y (float): The y-coordinate of the target point.

    Returns:
        tuple: The (x, y) pair from the QTable that is closest to the target point.
    """
    x = qtable[x_col]
    y = qtable[y_col]
    distances = np.sqrt((x - target_x)**2 + (y - target_y)**2)
    min_index = np.argmin(distances)

    return qtable[x_col][min_index], qtable[y_col][min_index]

from astropy.time import Time
import glob

def iso_date_to_JD(iso_date:str) -> float:
    iso_date = iso_date.replace("T", " ")
    t = Time(iso_date, format='iso')
    return t.jd

def calculate_light_curves(output_directory:str, cat_indicator:str, light_frame_indicator:str, n_radii:int, target_location:tuple, comparison_location:tuple, validation_location:tuple) -> tuple[list, list, list]:
    catalogue_files = glob.glob(output_directory + f'/*{cat_indicator}*')
    processed_light_files = glob.glob(output_directory + f'/*{light_frame_indicator}*')
    catalogue_files.sort()
    processed_light_files.sort()
    
    n_files = len(catalogue_files)
    n_time_stamps = len(processed_light_files)
    # if(n_files!=n_time_stamps):
    #     raise Exception("ERROR: Output light files list differs in length from output catalogue file list. \n --> Check to ensure that no files were moved or deleted.")
    target_lc=np.zeros((1+2*n_radii,n_files))
    comparison_lc=np.zeros((1+2*n_radii,n_files))
    validation_lc=np.zeros((1+2*n_radii,n_files))
    
    print("Calcluating target, comparison, and validation light curves.")
    
    '''first we get the time (JD) from the paralell list of light files, then sum the apertures'''
    
    for i, file in enumerate(catalogue_files):
        header = fits.getheader(processed_light_files[i-1])
        datestr = iso_date_to_JD(header['DATE-OBS'])

        target_lc[0,i] = datestr
        comparison_lc[0,i] = datestr
        validation_lc[0,i] = datestr
        
        catalogue = fits.getdata(file)
        
        x_source_locations = catalogue['x_shift']
        y_source_locations = catalogue['y_shift']
        
        #This is pretty inefficent but perhaps more efficent than using a star database, solving, and converting?
        target_distance_array = np.sqrt((x_source_locations - target_location[0])**2+(y_source_locations - target_location[1])**2)
        minimum_index = np.argmin(target_distance_array)
        #TODO: use a tolerance, assume correct FOR NOW
        distance_undertainty = target_distance_array[minimum_index]
        target_aper_arr = catalogue[minimum_index]
        #add the aperture sums to the first half of the array and their repective errors to the second half of the target lightcurve array
        for j in range(n_radii):
            target_lc[j+1,i]=target_aper_arr['aperture_sum_'+str(j)]
            target_lc[n_radii+j+1,i]=target_aper_arr['aperture_sum_err_'+str(j)]
        
        #repeat the process for the comparison star:
        comparison_distance_array = np.sqrt((x_source_locations - comparison_location[0])**2+(y_source_locations - comparison_location[1])**2)
        minimum_index_comp = np.argmin(comparison_distance_array)
        distance_undertainty = catalogue[minimum_index]
        comparison_aper_arr = catalogue[minimum_index_comp]
        for j in range(n_radii):
            comparison_lc[j+1,i]=comparison_aper_arr['aperture_sum_'+str(j)]
            comparison_lc[n_radii+j+1,i]=comparison_aper_arr['aperture_sum_err_'+str(j)]
        
        #and again for the validation star:
        validation_distance_array = np.sqrt((x_source_locations - validation_location[0])**2+(y_source_locations - validation_location[1])**2)
        minimum_index_vali = np.argmin(validation_distance_array)
        distance_undertainty = catalogue[minimum_index_vali]
        validation_aper_arr = catalogue[minimum_index_vali]
        for j in range(n_radii):
            validation_lc[j+1,i]=validation_aper_arr['aperture_sum_'+str(j)]
            validation_lc[n_radii+j+1,i]=validation_aper_arr['aperture_sum_err_'+str(j)]
        
    return (target_lc, comparison_lc, validation_lc)

def get_plotting_data(target_lc:list, comparison_lc:list, validation_lc:list, iaper:int) -> tuple[list, list, float, float, float, float, list]:
    iaper=6 # for iaper aperture
    lc_target_plot=target_lc[iaper+1,:]/comparison_lc[iaper+1,:]
    lc_validation_plot=validation_lc[iaper+1,:]/comparison_lc[iaper+1,:]
    #error calculation
    a1=1.0/comparison_lc[iaper+1,:]; e1=target_lc[iaper+10+1,:]
    a2=target_lc[iaper+1,:]/comparison_lc[iaper+1,:]**2; e2=comparison_lc[iaper+10+1,:]
    error_target=np.sqrt(a1**2*e1**2+a2**2*e2**2)
    
    a1=1.0/comparison_lc[iaper+1,:]; e1=validation_lc[iaper+10+1,:]
    a2=validation_lc[iaper+1,:]/comparison_lc[iaper+1,:]**2; e2=comparison_lc[iaper+10+1,:]
    error_valiation=np.sqrt(a1**2*e1**2+a2**2*e2**2)
    
    print('photerr for target/comparison:',np.median(error_target))
    print('photerr for validation/comparison:',np.median(error_valiation))
    idx=np.argmin(np.abs(target_lc[0,:]-51888.67))
    norm_targ=np.median(lc_target_plot[idx:])
    norm_vali=np.median(lc_validation_plot[idx:])
    time_axis_range=[np.min(target_lc[0,:]),np.max(target_lc[0,:])]
    return lc_target_plot, lc_validation_plot, error_target, error_valiation, norm_targ, norm_vali, time_axis_range

def plot_light_curve(jd:list, lc_target_plot:list, lc_validation_plot:list, norm_targ:float, norm_vali:float, time_axis_range:list, directory_out:str, transit_name:str, date:str, observer_name:str):
    plt.figure(figsize=(16,16))
    plt.scatter(jd[0,:],lc_target_plot/(1.005*norm_targ),color='black', marker='o',s=10,label="Target")
    plt.scatter(jd[0,:],lc_validation_plot/norm_vali-0.02,color='magenta', marker='o',s=10, label="Validation Star")
    plt.plot(time_axis_range,[1.0,1.0],'b-',linewidth=.5)
    plt.plot(time_axis_range,[.980,.980],'b-',linewidth=.5)
    plt.ylim([0.970,1.01])
    plt.xlabel("\nJulian Date (JD)",fontsize=15)
    plt.ylabel("Relative Flux", fontsize=15)
    plt.grid(True)
    plt.suptitle(f"\n  {transit_name}", fontsize=30)
    plt.title(f"{date}\nObserver: {observer_name}\n", fontsize=12)
    plt.legend()
    plt.savefig(directory_out+f"/{transit_name}")
    plt.show()
    to_csv(jd[0,:], lc_target_plot, lc_validation_plot, norm_targ, norm_vali, directory_out, f"{transit_name}_measurements")
    print(sigma_clipped_stats(2.5*np.log10(lc_validation_plot),sigma=3,maxiters=3))
    
def to_csv(jd:list, target_lc:list, validation_lc:list, norm_target:float, norm_vali:float, directory_out:str, filename:str):
    """
    Takes two arrays, creates a DataFrame, and saves it as a CSV file.
    """
    # Create a DataFrame from the arrays
    time_axis = np.array(jd)
    target_lc = np.array(target_lc)/norm_target
    validation_lc = np.array(validation_lc)/norm_vali
    comparison_lc = np.array(comparison_lc)
    
    data = {'Time Axis': time_axis, 'Target Flux': target_lc, 'Validation Flux': validation_lc, 'Comparison Flux': comparison_lc}
    df = pd.DataFrame(data)

    # Create the full file path
    file_path = os.path.join(directory_out, filename)

    # Save the DataFrame to a CSV file
    df.to_csv(file_path, index=False)
    print(f"CSV file created at: {file_path}")

def perform_photometry(light_frame_indicator:str, catalogue_indicator:str, output_dir:str, threshold_multiplier:float, target_radius:int, target_location:tuple, comparison_location:tuple, validation_location:tuple) -> tuple[list, list, list]:
    write_photometric_catalogues(light_frame_indicator, output_dir, threshold_multiplier)
    calc_shifts_update_catalogues(output_dir)
    target_lc, comparison_lc, validation_lc = calculate_light_curves(output_dir, catalogue_indicator, light_frame_indicator,n_radii=10, target_location=target_location, comparison_location=comparison_location, validation_location=validation_location)
    return (target_lc, comparison_lc, validation_lc)

def plot(target_lc:list, comparison_lc:list, validation_lc:list, output_dir:str, transit_name:str, date:str, observer_name:str) -> None:
    lc_target_plot, lc_validation_plot, error_target, error_valiation, norm_targ, norm_vali, time_axis_range = get_plotting_data(target_lc, comparison_lc, validation_lc, iaper=6)
    plot_light_curve(target_lc, lc_target_plot, lc_validation_plot, norm_targ, norm_vali, time_axis_range, output_dir, transit_name, date, observer_name)
    
#current constants
threshold_multiplier = 15.
#get the qtable with the Table.read funciton
#targets from the get closest pair function and initial/visual guesses
#TODO: automate
x_targ,y_targ = (2403.662364756954, 2018.2046627353204)
x_comp,y_comp = (1756.1089736736467, 2364.1375110432928)
x_vali,y_vali = (1988.9627767690627, 1765.0694999895554)
###plotting###
#these should be provided via txt file.
transit_name = "Qatar-5"
date = "09/05/2024"
observer_name = "Marina Skuban"
light_frame_indicator = "lrp"
output_dir = '/Users/spencerfreeman/Desktop/PersonalCS/CurrentPipeline/test_input/test_output'
catalogue_indicator = "cat"

if __name__ == "__main__":
    write_photometric_catalogues(light_frame_indicator, output_dir, threshold_multiplier)
    calc_shifts_update_catalogues(output_dir)
    target_lc, comparison_lc, validation_lc = calculate_light_curves(output_dir, catalogue_indicator, light_frame_indicator,n_radii=10, target_location=(x_targ,y_targ), comparison_location=(x_comp, y_comp), validation_location=(x_vali, y_vali))
    #plotting related calls/variables
    lc_target_plot, lc_validation_plot, error_target, error_valiation, norm_targ, norm_vali, time_axis_range = get_plotting_data(target_lc, comparison_lc, validation_lc, iaper=6)
    plot_light_curve(target_lc, lc_target_plot, lc_validation_plot, norm_targ, norm_vali, time_axis_range, output_dir, transit_name, date, observer_name)
    to_csv(target_lc[0,:], lc_target_plot, lc_validation_plot, norm_targ, norm_vali, output_dir, "Qatar-5.png")
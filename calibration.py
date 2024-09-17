import matplotlib.ticker as ticker
import os
import collections 
from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
from load_frames import *

import matplotlib.ticker as ticker
fig, (ax1, ax2) = plt.subplots(1,2)

def make_sub_dir(directory):
    new_directory = directory + "/processed_by_pipeline"
    if(os.path.exists(new_directory) == False):
        os.makedirs(new_directory)
    return new_directory

new_directory = make_sub_dir(directory)

def median_flats(flats, biases, total_flats, total_biases, directory, new_directory):
   
    make_sub_dir(directory)
    
    if(len(flats) == 0):
        print("***image load failure, please check path and retry.***")
    #case in which only one flat is present
    elif(len(flats) == 1):
        
        bright_value = get_bright_value(median_flat)
        median_bias = np.median(biases)
        master_flat_pixel_array = (median_flat - median_bias)/bright_value
        ax1.imshow(master_flat_pixel_array)
        ax1.set_title("Master Flat: {0}".format(transit_name))
        return master_flat_pixel_array
    
    elif(len(flats)>1):
        '''
        *to build a master flat image we will take median of the flats and then subtract the average of the biases.*
        we should probably subtract and then take the median...
        '''
        median_flat = np.median(flats, axis=0)
        bright_value = get_bright_value(median_flat)
        median_bias = np.median(biases)
        master_flat_pixel_array = (median_flat - median_bias)/bright_value
        ax1.imshow(master_flat_pixel_array)
        write_to_directory(master_flat_pixel_array, 'mflat.fits', new_directory)
        ax1.set_title("Master Flat: {0}".format(transit_name))
        return master_flat_pixel_array
    
def median_biases(biases, total_biases, directory, new_directory):
    make_sub_dir(directory)
    if(len(biases) == 0):
        print("***image load failure, please check path and retry.***")
    elif(len(biases) == 1):
        master_bias_pixel_array = biases[0][0].data
        plt.imshow(master_bias)
        ax2.set_title("Master Bias: {0}".format(transit_name))
        ax2.yaxis.set_major_locator(ticker.NullLocator())
        write_to_directory(master_bias_pixel_array, 'mbias.fits', new_directory)
        return master_bias_pixel_array
    elif(len(biases) > 1):
        master_bias_pixel_array = np.median(biases, axis=0)
        ax2.imshow(master_bias_pixel_array)
        ax2.set_title("Master Bias: {0}".format(transit_name))
        #hide the tick marks on the master bias plot
        ax2.yaxis.set_major_locator(ticker.NullLocator())
        write_to_directory(master_bias_pixel_array, 'mbias.fits', new_directory)
        return master_bias_pixel_array

def get_bright_value(master_flat_pixel_array_pre_sub):
    values = []
    dimension = int(return_dimensions(master_flat_pixel_array_pre_sub)[0])
    dist = 100
    for i in range(dimension//2-dist, dimension//2+dist):
        for j in range(dimension//2-dist, dimension//2+dist):
            values.append(master_flat_pixel_array_pre_sub[i][j])
    median_bright = np.median(values)
    return median_bright
    
def fits_to_array(fits_list):
    pixel_arrays = []
    for file in fits_list:
        pixel_arrays.append(file[0].data)
    return pixel_arrays

def write_to_directory(master_pixel_array, filename, new_directory):
    path = new_directory
    hdu = fits.PrimaryHDU(master_pixel_array)
    hdulist = fits.HDUList([hdu])
    hdulist.writeto(os.path.join(new_directory, filename), overwrite=True)
    
def return_dimensions(pixel_2d_array):
    return ([len(pixel_2d_array), len(pixel_2d_array[0])])

if __name__ == "__main__":
    flat_pixel_array_list = fits_to_array(flats)
    bias_pixel_array_list = fits_to_array(biases)
    lights_pixel_array_list = fits_to_array(lights)
    master_flat_pixel_array = median_flats(flat_pixel_array_list, bias_pixel_array_list, len(flats), len(biases), directory, new_directory)
    master_bias_pixel_array = median_biases(bias_pixel_array_list, len(biases), directory, new_directory)
    plt.show()
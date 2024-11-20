import os
from astropy.io import fits
from ccdproc import ImageFileCollection

directory = '/Users/spencerfreeman/Desktop/stepUp/2024-09-4-skuban'
transit_name = 'Qatar-5b'

light_frame_indicator = "lrp"
flat_frame_indicator = "frp.fit"
bias_frame_indicator = "bias.fit"

def print_guidance(name_indicator, directory):
    print("+------------------------------------------------------------------------------------------------------------+")
    print("loading images from {0} including the string {1}...".format(directory, name_indicator))
    print("+------------------------------------------------------------------------------------------------------------+")

#running method
#load light frames loads actual fits files. to accsess the pixel array we must use [0].data on each object in the lights array. 
def load_light_frames(directory, light_frame_indicator):
    light_frame_list = []
    print_guidance(light_frame_indicator, directory)
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and light_frame_indicator in filename:
            hdu_list = fits.open(f)
            light_frame_list.append(hdu_list)
    return light_frame_list

def load_bias_frames(directory, bias_frame_indicator):
    print_guidance(bias_frame_indicator, directory)
    bias_frame_list = []
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and bias_frame_indicator in filename:
            hdu_list = fits.open(f)
            bias_frame_list.append(hdu_list)
    return bias_frame_list

def load_flat_frames(directory, flat_frame_indicator):
    print_guidance(flat_frame_indicator, directory)
    flat_frame_list = []
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and flat_frame_indicator in filename:
            hdu_list = fits.open(f)
            flat_frame_list.append(hdu_list)
    return flat_frame_list

#an alternative to using the os module for loading images, returns all three lists.
def return_light_hdu_lists(directory):
    im_collection = ImageFileCollection(directory)
    light_hdu_lists = []
    bias_hdu_lists = []
    flat_hdu_lists = []
    for a_lrp in im_collection.hdus(imagetyp='Light Frame'):
        light_hdu_lists.append(a_lrp)
    for b_bias in im_collection.hdus(imagetyp='Bias Frame'):
        bias_hdu_lists.append(b_bias)
    for f_frp in im_collection.hdus(imagetyp='Flat Field'):
        flat_hdu_lists.append(f_frp)
    return light_hdu_lists, bias_hdu_lists, flat_hdu_lists

if __name__ == "__main__":
    lights = load_light_frames(directory, light_frame_indicator)
    flats = load_flat_frames(directory, flat_frame_indicator)
    biases = load_bias_frames(directory, bias_frame_indicator)
    print('total lights loaded: {0}'.format(len(lights)))
    print('total flats loaded: {0}'.format(len(flats)))
    print('total biases loaded: {0}'.format(len(biases)))
    print(biases[0][0].header)
        

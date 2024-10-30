import os
import collections 
from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np

directory = '/Users/spencerfreeman/Desktop/stepUp/freeman2024-09-03'
transit_name = 'WASP-135b'

light_frame_indicator = "lrp"
flat_frame_indicator = "frp.fit"
bias_frame_indicator = "bias.fit"

'''
if it turns out we need more information from the fits images, then the file objects must be adjusted in these methods.
'''
#helper method
def print_guidance(name_indicator, directory):
    print("+------------------------------------------------------------------------------------------------------------+")
    print("loading images from {0} including the string {1}...".format(directory, name_indicator))
    print("+------------------------------------------------------------------------------------------------------------+")

#running method
#load light frames loads actual fits files. to accsess the pixel array we must use [0].data on each object in the lights array. 
def load_light_frames(directory, light_frame_indicator):
    light_frame_linkedlist = collections.deque()
    print_guidance(light_frame_indicator, directory)
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and light_frame_indicator in filename:
            file = fits.open(f)
            light_frame_linkedlist.append(file)
    return light_frame_linkedlist

def load_bias_frames(directory, bias_frame_indicator):
    print_guidance(bias_frame_indicator, directory)
    bias_frame_linkedlist = collections.deque()
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and bias_frame_indicator in filename:
            file = fits.open(f)
            bias_frame_linkedlist.append(file)
    return bias_frame_linkedlist

def load_flat_frames(directory, flat_frame_indicator):
    print_guidance(flat_frame_indicator, directory)
    flat_frame_linkedlist = collections.deque()
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if os.path.isfile(f) and flat_frame_indicator in filename:
            file = fits.open(f)
            flat_frame_linkedlist.append(file)
    return flat_frame_linkedlist

lights = load_light_frames(directory, light_frame_indicator)
flats = load_flat_frames(directory, flat_frame_indicator)
biases = load_bias_frames(directory, bias_frame_indicator)

if __name__ == "__main__":
    print('total lights loaded: {0}'.format(len(lights)))
    print('total flats loaded: {0}'.format(len(flats)))
    print('total biases loaded: {0}'.format(len(biases)))
        

from astropy.stats import mad_std
from astropy import units as u
from astropy.nddata import CCDData
from pathlib import Path
from astropy.coordinates import SkyCoord
from astropy.io import fits
import ccdproc as ccdp
import matplotlib.pyplot as plt
import numpy as np
import glob

class Calibration:
    def __init__(self, directory: str, flip: bool):
        self.directory = directory
        self.flip = flip

    def _make_subdir(self):
        calibrated_data = Path(self.directory, 'master_frames_test')
        calibrated_data.mkdir(exist_ok=True)
        return calibrated_data

    @staticmethod
    def inv_median(a) -> int:
        return 1 / np.median(a)

    def create_master_frames(self):
        main_path = Path(self.directory)
        files = ccdp.ImageFileCollection(main_path)
        biases = files.files_filtered(imagetyp='Bias Frame', include_path=True)
        flats = files.files_filtered(imagetyp='Flat Field', include_path=True)
        calibrated_data = self._make_subdir()
        bias_data = []
        for bias_file in biases:
            bias_frame = CCDData.read(bias_file, unit=u.adu)
            bias_data.append(bias_frame)
        master_bias = ccdp.combine(bias_data, method='average', sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                                    sigma_clip_func=np.ma.median, sigma_clip_dev_func=mad_std, mem_limit=350e6)
        master_bias.meta['combined'] = True
        master_bias.data = master_bias.data.astype('float32')
        if self.flip:
            master_bias.data = np.flipud(master_bias.data)
        master_bias.write(calibrated_data / 'master_bias.fit', overwrite=True)
        flat_data = []
        for flat_file in flats:
            flat_field = CCDData.read(flat_file, unit=u.adu)
            flat_data.append(flat_field)
        master_flat = ccdp.combine(flat_data, method='average', scale=self.inv_median, sigma_clip=True, sigma_clip_low_thresh=5, sigma_clip_high_thresh=5,
                                    sigma_clip_func=np.ma.median, signma_clip_dev_func=mad_std, mem_limit=350e6)
        master_flat.meta['combined'] = True
        if self.flip:
            master_flat.data = np.flipud(master_flat.data)
        master_flat.data = master_flat.data.astype('float32')
        master_flat.write(calibrated_data / 'master_flat.fit', overwrite=True)
        del files
        return master_bias, master_flat

    def calibrate_light_frames(self, transit_name: str, master_bias: CCDData, master_flat: CCDData, target_coords_wcs: list):
        main_path = Path(self.directory)
        files = ccdp.ImageFileCollection(main_path)
        FOCALLEN = 3962.3999023437500  # mm
        PIXELSIZE = 9  # um
        pixscale = 206.265 * (PIXELSIZE / FOCALLEN)
        c = SkyCoord(target_coords_wcs[0], target_coords_wcs[1], frame='icrs', unit=(u.hourangle, u.degree))
        ra = c.ra.degree; dec = c.dec.degree
        gain, readout_noise = self.get_gain_readout_noise("bias", "frp")
        lights = files.files_filtered(imagetyp='Light Frame', include_path=True)
        counter = 1
        light_frames = []
        for light in lights:
            print(f"Reducing light frame {counter}/{len(lights)}")
            light_frame = CCDData.read(light, unit=u.adu)
            reduced = ccdp.ccd_process(light_frame, master_bias=master_bias, master_flat=master_flat)
            self.edit_header(reduced, ra, dec, pixscale, gain, readout_noise)
            if self.flip:
                reduced.data = np.flipud(reduced.data)
            reduced.data = reduced.data.astype('float32')
            light_frames.append(reduced)
            reduced.write(f"{self.directory}/test_output/{transit_name}_lrp_{counter}.fit", overwrite=True)
            counter += 1
        del files
        return light_frames

    def edit_header(self, reduced, ra, dec, pixscale, gain, readout_noise):
        reduced.meta['epoch'] = 2000.0
        reduced.meta['CRVAL1'] = ra
        reduced.meta['CRVAL2'] = dec
        reduced.meta['CRPIX1'] = reduced.meta['NAXIS1'] / 2.0
        reduced.meta['CRPIX2'] = reduced.meta['NAXIS2'] / 2.0
        reduced.meta['CDELT1'] = -pixscale / 3600.0
        reduced.meta['CDELT2'] = pixscale / 3600.0
        reduced.meta['CTYPE1'] = 'RA---TAN'
        reduced.meta['CTYPE2'] = 'DEC--TAN'
        reduced.meta['GAIN'] = (gain, 'GAIN in e-/ADU')
        reduced.meta['RDNOISE'] = (readout_noise, 'readout noise in electrons')

    def get_gain_readout_noise(self, bias_indicator: str, flat_indicator: str) -> tuple:
        bias_list = glob.glob(self.directory + f"/*{bias_indicator}*")
        flat_list = glob.glob(self.directory + f"/*{flat_indicator}*")
        print(len(bias_list))
        print(len(flat_list))
        bias_data = []
        flat_data = []
        for bias_file in bias_list:
            data = fits.getdata(bias_file)[1500-256:1500+256, 1500-256:1500+256]
            bias_data.append(data)
        for flat_file in flat_list:
            data = fits.getdata(flat_file)[1500-256:1500+256, 1500-256:1500+256]
            flat_data.append(data)
        bias_combined = np.median(bias_data, axis=0)
        flat_combined = np.median(flat_data, axis=0)
        mean_flat = np.mean(flat_combined)
        mean_bias = np.mean(bias_combined)
        std_flat = np.std(flat_combined)
        std_bias = np.std(bias_combined)
        gain = (mean_flat - mean_bias) / (std_flat**2 - std_bias**2)
        readnoise = gain * std_bias / np.sqrt(2)
        print(f"gain: {gain}, readout noise: {readnoise}")
        return (gain, readnoise)

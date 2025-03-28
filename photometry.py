from astropy.stats import sigma_clipped_stats, SigmaClip
from photutils.background import Background2D, SExtractorBackground
from photutils.detection import IRAFStarFinder
from photutils.segmentation import detect_sources
from astropy.io import fits
from photutils.utils import calc_total_error
from photutils.aperture import CircularAperture, aperture_photometry
from astropy.table import Table
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import glob
from astropy.time import Time

class Photometry:
    def __init__(self, output_dir: str, threshold_multiplier: float, catalogue_indicator: str, light_frame_indicator: str, n_radii: int = 10):
        self.output_dir = output_dir
        self.threshold_multiplier = threshold_multiplier
        self.catalogue_indicator = catalogue_indicator
        self.light_frame_indicator = light_frame_indicator
        self.n_radii = n_radii
        self.radii = [3, 4, 5, 6, 8, 10, 12, 15, 20, 25]

    def _background(self, file: str):
        data = fits.getdata(file)
        mean, _, std = sigma_clipped_stats(data, sigma=3.0)
        segm = detect_sources(data - mean, 3 * std, npixels=5)
        bool_array = segm.data != 0
        sigma_clip = SigmaClip(sigma=3.)
        bkg_estimator = SExtractorBackground()
        bkg = Background2D(data, (64, 64), mask=bool_array, filter_size=(3, 3), sigma_clip=sigma_clip, bkg_estimator=bkg_estimator)
        return bkg

    def write_photometric_catalogues(self):
        lights_processed = glob.glob(f'{self.output_dir}/*{self.light_frame_indicator}*')
        lights_processed.sort()
        total = len(lights_processed)
        for i, file in enumerate(lights_processed):
            data = fits.getdata(file)
            print(f"Aperture photometry on all objects: file {i+1}/{total}")
            rootname, _ = os.path.splitext(file)
            catfile = f'{self.output_dir}/{i+1}-cat.fits'
            print(file)
            bkg = self._background(file)
            IRAFfind = IRAFStarFinder(fwhm=3.0, threshold=self.threshold_multiplier * bkg.background_rms_median,
                                       exclude_border=True, sharplo=0.5, sharphi=2.0, roundlo=0.0, roundhi=0.7)
            sources = IRAFfind(data - bkg.background)
            positions = [(ix, iy) for ix, iy in zip(sources['xcentroid'], sources['ycentroid'])]
            apertures = [CircularAperture(positions, r=r) for r in self.radii]
            gain = 0.242759602
            error = calc_total_error(data - bkg.background, bkg.background_rms, gain)
            aper_phot = aperture_photometry(data - bkg.background, apertures, error=error)
            print(f"Total sources detected: {len(aper_phot)}")
            aper_phot.write(catfile, overwrite=True)

    def calc_shifts_update_catalogues(self):
        catalogue_files = glob.glob(f'{self.output_dir}/*cat.fits')
        catalogue_files.sort()
        x1 = []
        y1 = []
        reference_catalogue = Table.read(catalogue_files[0])
        for i, catalogue in enumerate(catalogue_files):
            if i == 0:
                reference_catalogue = Table.read(catalogue)
                x1 = reference_catalogue['xcenter']
                y1 = reference_catalogue['ycenter']
                if 'x_shift' not in reference_catalogue.colnames:
                    xcol = Table.Column(x1, name='x_shift')
                    ycol = Table.Column(y1, name='y_shift')
                    reference_catalogue.add_columns([xcol, ycol])
                else:
                    reference_catalogue['x_shift'] = x1
                    reference_catalogue['y_shift'] = y1
                reference_catalogue.write(catalogue, overwrite=True)
                print("Initial iteration complete, reference catalogue updated.")
            else:
                catalogue_of_interest = Table.read(catalogue)
                n_catalogue_OI = len(catalogue_of_interest)
                x2 = catalogue_of_interest['xcenter']
                y2 = catalogue_of_interest['ycenter']
                XX = []
                YY = []
                for j in range(n_catalogue_OI):
                    XX.extend((x1 - x2[j]))
                    YY.extend((y1 - y2[j]))
                XX = np.array(XX)
                YY = np.array(YY)
                xhist, xbins = np.histogram(XX, range=[-200, 200], bins=400)
                yhist, ybins = np.histogram(YY, range=[-200, 200], bins=400)
                idx = np.argmax(xhist)
                xshift_0 = (xbins[idx] + xbins[idx + 1]) / 2.0
                idx = np.argmax(yhist)
                yshift_0 = (ybins[idx] + ybins[idx + 1]) / 2.0
                print(f"Initial shift X (Iteration {i}): {xshift_0}, Initial shift Y: {yshift_0}")
                mask = (np.abs(XX - xshift_0) < 3) & (np.abs(YY - yshift_0) < 3)
                print("Mask sum: ", mask.sum())
                xshift_finetuned = np.median(XX[mask])
                yshift_finetuned = np.median(YY[mask])
                print(f"Finetuned Shift (Iteration {i}): ", xshift_finetuned, yshift_finetuned)
                if 'x_shift' not in catalogue_of_interest.colnames:
                    xcol = Table.Column(x2 + xshift_finetuned, name='x_shift')
                    ycol = Table.Column(y2 + yshift_finetuned, name='y_shift')
                    catalogue_of_interest.add_columns([xcol, ycol])
                else:
                    catalogue_of_interest['x_shift'] = x2 + xshift_finetuned
                    catalogue_of_interest['y_shift'] = y2 + yshift_finetuned
                catalogue_of_interest.write(catalogue, overwrite=True)

    def _iso_date_to_JD(self, iso_date: str) -> float:
        iso_date = iso_date.replace("T", " ")
        t = Time(iso_date, format='iso')
        return t.jd

    def calculate_light_curves(self, target_location: tuple, comparison_location: tuple, validation_location: tuple) -> tuple:
        catalogue_files = glob.glob(self.output_dir + f'/*{self.catalogue_indicator}*')
        processed_light_files = glob.glob(self.output_dir + f'/*{self.light_frame_indicator}*')
        catalogue_files.sort()
        processed_light_files.sort()
        n_files = len(catalogue_files)
        target_lc = np.zeros((1 + 2 * self.n_radii, n_files))
        comparison_lc = np.zeros((1 + 2 * self.n_radii, n_files))
        validation_lc = np.zeros((1 + 2 * self.n_radii, n_files))
        print("Calculating target, comparison, and validation light curves.")
        for i, file in enumerate(catalogue_files):
            header = fits.getheader(processed_light_files[i - 1])
            datestr = self._iso_date_to_JD(header['DATE-OBS'])
            target_lc[0, i] = datestr
            comparison_lc[0, i] = datestr
            validation_lc[0, i] = datestr
            catalogue = fits.getdata(file)
            x_source_locations = catalogue['x_shift']
            y_source_locations = catalogue['y_shift']
            target_distance_array = np.sqrt((x_source_locations - target_location[0])**2 + (y_source_locations - target_location[1])**2)
            minimum_index = np.argmin(target_distance_array)
            target_aper_arr = catalogue[minimum_index]
            for j in range(self.n_radii):
                target_lc[j + 1, i] = target_aper_arr['aperture_sum_' + str(j)]
                target_lc[self.n_radii + j + 1, i] = target_aper_arr['aperture_sum_err_' + str(j)]
            comparison_distance_array = np.sqrt((x_source_locations - comparison_location[0])**2 + (y_source_locations - comparison_location[1])**2)
            minimum_index_comp = np.argmin(comparison_distance_array)
            comparison_aper_arr = catalogue[minimum_index_comp]
            for j in range(self.n_radii):
                comparison_lc[j + 1, i] = comparison_aper_arr['aperture_sum_' + str(j)]
                comparison_lc[self.n_radii + j + 1, i] = comparison_aper_arr['aperture_sum_err_' + str(j)]
            validation_distance_array = np.sqrt((x_source_locations - validation_location[0])**2 + (y_source_locations - validation_location[1])**2)
            minimum_index_vali = np.argmin(validation_distance_array)
            validation_aper_arr = catalogue[minimum_index_vali]
            for j in range(self.n_radii):
                validation_lc[j + 1, i] = validation_aper_arr['aperture_sum_' + str(j)]
                validation_lc[self.n_radii + j + 1, i] = validation_aper_arr['aperture_sum_err_' + str(j)]
        return (target_lc, comparison_lc, validation_lc)

    def get_plotting_data(self, target_lc: list, comparison_lc: list, validation_lc: list, iaper: int) -> tuple:
        iaper = 6
        lc_target_plot = target_lc[iaper + 1, :] / comparison_lc[iaper + 1, :]
        lc_validation_plot = validation_lc[iaper + 1, :] / comparison_lc[iaper + 1, :]
        a1 = 1.0 / comparison_lc[iaper + 1, :]; e1 = target_lc[iaper + 10 + 1, :]
        a2 = target_lc[iaper + 1, :] / comparison_lc[iaper + 1, :]**2; e2 = comparison_lc[iaper + 10 + 1, :]
        error_target = np.sqrt(a1**2 * e1**2 + a2**2 * e2**2)
        a1 = 1.0 / comparison_lc[iaper + 1, :]; e1 = validation_lc[iaper + 10 + 1, :]
        a2 = validation_lc[iaper + 1, :] / comparison_lc[iaper + 1, :]**2; e2 = comparison_lc[iaper + 10 + 1, :]
        error_valiation = np.sqrt(a1**2 * e1**2 + a2**2 * e2**2)
        print('photerr for target/comparison:', np.median(error_target))
        print('photerr for validation/comparison:', np.median(error_valiation))
        idx = np.argmin(np.abs(target_lc[0, :] - 51888.67))
        norm_targ = np.median(lc_target_plot[idx:])
        norm_vali = np.median(lc_validation_plot[idx:])
        time_axis_range = [np.min(target_lc[0, :]), np.max(target_lc[0, :])]
        return lc_target_plot, lc_validation_plot, error_target, error_valiation, norm_targ, norm_vali, time_axis_range

    def plot_light_curve(self, jd: list, lc_target_plot: list, lc_validation_plot: list, comparison_lc: list, norm_targ: float,
                         norm_vali: float, iaper: int, time_axis_range: list, transit_name: str, date: str, observer_name: str):
        plt.figure(figsize=(16, 16))
        plt.scatter(jd[0, :], lc_target_plot / (1.005 * norm_targ), color='black', marker='o', s=10, label="Target")
        plt.scatter(jd[0, :], lc_validation_plot / norm_vali - 0.02, color='magenta', marker='o', s=10, label="Validation Star")
        plt.plot(time_axis_range, [1.0, 1.0], 'b-', linewidth=0.5)
        plt.plot(time_axis_range, [0.980, 0.980], 'b-', linewidth=0.5)
        plt.ylim([0.970, 1.01])
        plt.xlabel("\nJulian Date (JD)", fontsize=15)
        plt.ylabel("Relative Flux", fontsize=15)
        plt.grid(True)
        plt.suptitle(f"\n  {transit_name}", fontsize=30)
        plt.title(f"{date}\nObserver: {observer_name}\n", fontsize=12)
        plt.legend()
        plt.savefig(self.output_dir + f"/{transit_name}")
        plt.show()
        self.to_csv(jd[0, :], lc_target_plot, lc_validation_plot, comparison_lc, norm_targ, norm_vali, iaper, f"{transit_name}_measurements")
        print(sigma_clipped_stats(2.5 * np.log10(lc_validation_plot), sigma=3, maxiters=3))

    def to_csv(self, jd: list, target_lc: list, validation_lc: list, comparison_lc: list, norm_target: float,
               norm_vali: float, iaper: int, filename: str):
        time_axis = np.array(jd)
        target_lc = np.array(target_lc) / norm_target
        validation_lc = np.array(validation_lc) / norm_vali
        comparison_lc = np.array(comparison_lc[iaper + 1, :])
        data = {'Time Axis': time_axis, 'Target Flux': target_lc, 'Validation Flux': validation_lc, 'Comparison Flux': comparison_lc}
        df = pd.DataFrame(data)
        file_path = os.path.join(self.output_dir, filename)
        df.to_csv(file_path, index=False)
        print(f"CSV file created at: {file_path}")

    def perform_photometry(self, target_location: tuple, comparison_location: tuple, validation_location: tuple) -> tuple:
        self.write_photometric_catalogues()
        self.calc_shifts_update_catalogues()
        target_lc, comparison_lc, validation_lc = self.calculate_light_curves(target_location, comparison_location, validation_location)
        return (target_lc, comparison_lc, validation_lc)

    def plot(self, target_lc: list, comparison_lc: list, validation_lc: list, iaper: int, transit_name: str,
             date: str, observer_name: str) -> None:
        lc_target_plot, lc_validation_plot, error_target, error_valiation, norm_targ, norm_vali, time_axis_range = self.get_plotting_data(target_lc, comparison_lc, validation_lc, iaper)
        self.plot_light_curve(target_lc, lc_target_plot, lc_validation_plot, comparison_lc, norm_targ, norm_vali, iaper, time_axis_range, transit_name, date, observer_name)
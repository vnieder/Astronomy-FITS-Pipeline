# Astro_Fits_Pipeline
Image pipeline equipped for calibration and processing of FITS images. Analysis performed using differential photometric techniques. Plate solve for WCS headers using Astrometry.net API to be supported.
- production of exoplanet transit light curves is the primary purpose of this pipeline.
- development of graphical user interface and existing features in progress.
- ideally, the final prodict will support analysis of existing tess data with libraries such as lightkurve and astropy, as well as personal observation data.
- this program should function in a manner similar to AstroImageJ, in a condensed manner.

## Data and Output
- Medians of flat and bias frames are computed and plotted as shown below:

![image](./static/master_frames.png)

- Comparison of uncalibrated and calibrated images, respectively (AstroImageJ window):
  
![image](./static/comparison.png)

- Current adjustments remove some background, and apply reasonable lens/CCD corrections.
- Vignetting is visually reduced, as well as haze.

![image](./static/sp.png)

![image](./static/test.png)

- Pipeline produces both seeing profiles and cumulative flux plots of target and comparison star.

![image](./static/curvev1.png)

- Results from the first full usage trial indicate the need for relative flux calculation refinement, outlier considerations, and a method of target location invoving WCS transformations rather than loose pixel math.
- A scientific method for deterining aperture placements and comparison stars is also necessary.

## CSV Functionality
- CSV files of measurements (built by standalone pipelines) can also be analyzed via the csv_functionality script.
- This can be utilized for testing purposes as well as confirmation of pipeline accuracy.
- To ensure proper function, user must provide a file with a relative flux measurement and some type of time series (JD, MJD, etc...)
- CSV files containing associated quantities (relative flux, comparison flux, target flux) are also created and saved locally

## Astrometry.net API for WCS Retrieval
- Currently calls generate an unformatted FITS header
- Header will ideally be written to the given FITS file for later use in the stacking and star location features.

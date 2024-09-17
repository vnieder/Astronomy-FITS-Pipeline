# Astro_Fits_Pipeline
Image pipeline equipped for calibration and processing of FITS images. Analysis performed using differential photometric techniques. Plate solve for WCS headers using Astrometry.net API to be supported.
- production of exoplanet transit light curves is the primary purpose of this pipeline.
- development of graphical user interface and existing features in progress.
- ideally, the final prodict will support analysis of existing tess data with libraries such as lightkurve and astropy, as well as personal observation data.
- this program should function in a manner similar to AstroImageJ, in a condensed manner.

## Data and Output
- Medians of flat and bias frames are computed and plotted as shown below:

![image](./static/master_frames.png)

- Light frames can be displayed in a similar manner:
  
![image](./static/light_frame.png)

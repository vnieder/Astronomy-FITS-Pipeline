from astroquery.astrometry_net import AstrometryNet
from load_frames import *

''' 
This is a very simple way to access the Astrometry.net plate solving API. 
Some important details to note:
- user must create an account at https://nova.astrometry.net to recieve an account/key.
- server, key, and user information must be stored in users astrometry configuration file which may or may not exist automaticaly...
- navigate to $HOME/.astropy/config/astroquery.cfg (or create the file if it doesen't exist) and format in the following manner:
+-----------------------------------------------------------------------------------------------------------------------------------+
[astrometry_net]

## The Astrometry.net API key.
api_key = XXXXXXXXXX

## Name of server
server = http://nova.astrometry.net

## Default timeout for connecting to server
timeout = 120
+-----------------------------------------------------------------------------------------------------------------------------------+
(from documentation: https://astroquery.readthedocs.io/en/latest/astrometry_net/astrometry_net.html#module-astroquery.astrometry_net)

- the wcs header returned from this function is an astropy fits Header. 
- this will later be applied to processed light files when file formatting issues are resolved.
'''

#user defined file path
filepath = '/Users/spencerfreeman/Desktop/stepUp/freeman2024-09-03/WASP-135b-0001_lrp.fit'
filepath1 = '/Users/spencerfreeman/Desktop/stepUp/freeman2024-09-03/WASP-135b-0002_lrp.fit'
filepath2 = '/Users/spencerfreeman/Desktop/stepUp/freeman2024-09-03/WASP-135b-0003_lrp.fit'

paths = [filepath, filepath1, filepath2]

ast = AstrometryNet()
header_list = []

def plate_solve_frame_list(paths):
    for path in paths:
        solve_for_wcs(path)
    return len(header_list)

def solve_for_wcs(file_path):
    wcs_header = ast.solve_from_image(file_path, force_image_upload=True)
    header_list.append(wcs_header)
    print(wcs_header)
    return wcs_header

if __name__ == "__main__":
    solve_for_wcs(filepath)
    
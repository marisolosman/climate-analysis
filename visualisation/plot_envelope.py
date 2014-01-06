"""
Filename:     plot_envelope.py
Author:       Damien Irving, d.irving@student.unimelb.edu.au
Description:  Plot wave envelope and associated wind and streamfunction anomalies

"""

import os
import sys
import argparse

module_dir = os.path.join(os.environ['HOME'], 'visualisation')
sys.path.insert(0, module_dir)
import plot_map

module_dir2 = os.path.join(os.environ['HOME'], 'modules')
sys.path.insert(0, module_dir2)
import coordinate_rotation as rot
import netcdf_io as nio

import numpy
import cdms2
import MV2


def extract_data(inargs):
    """Extract input data and check that time axes match"""

    env_data = nio.InputData(inargs.env_file, inargs.env_var, 
                             **nio.dict_filter(vars(inargs), ['time', 'region']))
    env_times = env_data.data.getTime().asComponentTime()    

    opt_data = {}
    for opt in ['uwind', 'vwind', 'sf']:    
        try:
            opt_data[opt] = nio.InputData(eval('inargs.'+opt+'[0]'), 
                                          eval('inargs.'+opt+'[1]'), 
                                          **nio.dict_filter(vars(inargs), ['time', 'region']))
        except AttributeError:
            opt_data[opt] = None
    
    if opt_data[opt]:
        assert opt_data[opt].data.getTime().asComponentTime() == env_times, \
        'Time axes must be the same for all input data'

    return env_data, opt_data['uwind'], opt_data['vwind'], opt_data['sf']


def restore_env(indata_env, inargs):
    """Restore the rotated envelope data to a typical lat/lon grid"""
    
    lat_axis = indata_env.data.getLatitude()
    lon_axis = indata_env.data.getLongitude()
    lats, lons = nio.coordinate_pairs(lat_axis[:], lon_axis[:])
    grid = indata_env.data.getGrid()
    new_np = [inargs.np_lat, inargs.np_lon]
    pm_point = [inargs.pm_lat, inargs.pm_lon]
    
    env_restored = rot.switch_regular_axes(indata_env.data, lats, lons, 
                                           lat_axis[:], lon_axis[:],
                                           new_np, pm_point=pm_point, invert=False)
    
    if 't' in indata_env.data.getOrder():
        axis_list = [indata_env.data.getTime(), lat_axis, lon_axis]
    else: 
        axis_list = [lat_axis, lon_axis]
    
    env_restored = cdms2.createVariable(env_restored, grid=grid, axes=axis_list)
    
    return env_restored
 

def main(inargs):
    """Create the plot"""

    # Read input data #

    indata_env, indata_u, indata_v, indata_sf = extract_data(inargs) 

    # Restore env data to standard lat/lon grid #

    env_restored = restore_env(indata_env, inargs)

    # Plot every time step #
   
    if inargs.timescale == 'monthly':
        tick_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
	keyval = 5
	quiv_scale = 200
	quiv_width = 0.002
    else:
        tick_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
	keyval = 10
	quiv_scale = 300
	quiv_width = 0.002

    for date in indata_env.data.getTime().asComponentTime():
        year, month, day = str(date).split(' ')[0].split('-')
	if inargs.timescale == 'monthly':
	    date_abbrev = year+'-'+month
	else:
	    date_abbrev = year+'-'+month+'-'+day
	    
        env_data = [env_restored(time=(date, date_abbrev), squeeze=1),]
        u_data = [indata_u.data(time=(date, date_abbrev), squeeze=1),] if indata_u else None
        v_data = [indata_v.data(time=(date, date_abbrev), squeeze=1),] if indata_v else None
        sf_data = [indata_sf.data(time=(date, date_abbrev), squeeze=1),] if indata_sf else None

        title = 'Wave envelope, 250hPa wind & sf anomaly, %s' %(date_abbrev)
        ofile = '%s_%s.png' %(inargs.ofile, date_abbrev)

        plot_map.multiplot(env_data,
		           ofile=ofile,
		           title=title,
			   region=inargs.region,
		           units='$m s^{-1}$',
                           draw_axis=True,
		           delat=30, delon=30,
		           contour=True,
		           ticks=tick_list, discrete_segments=inargs.segments, colourbar_colour=inargs.palette,
        	           contour_data=sf_data, contour_ticks=inargs.sf_ticks,
		           uwnd_data=u_data, vwnd_data=v_data, quiver_thin=9, key_value=keyval,
		           quiver_scale=quiv_scale, quiver_width=quiv_width,
        	           projection=inargs.projection, 
        	           extend='max',
			   search_paths=inargs.search_paths,
        	           image_size=inargs.image_size)
        
        tick_list = tick_list[0: -1]   # Fix for weird thing where it keeps appending to 
	                               # the end of the ticks list, presumably due to the 
				       # extend = 'max' 


if __name__ == '__main__':

    extra_info="""
example (vortex.earthsci.unimelb.edu.au):
    /usr/local/uvcdat/1.2.0rc1/bin/cdat plot_envelope.py
    /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260.nc
    env 20 260 0 0 daily 
    --sf /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/sf_Merra_250hPa_daily-anom-wrt-all_native.nc sf
    --ofile /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/figures/env/vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np26-260
    --time 1981-06-01 1981-06-30 none
    --search_paths 20 260 225 335 -10 10 5
"""
  
    description='Plot wave envelope and associated wind and streamfunction anomalies'
    parser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info, 
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("env_file", type=str, help="envelope file")
    parser.add_argument("env_var", type=str, help="envelope variable")
    parser.add_argument("np_lat", type=float, help="north pole latitude used for envelope extraction")
    parser.add_argument("np_lon", type=float, help="north pole longitude used for envelope extraction")
    parser.add_argument("pm_lat", type=float, help="prime meridian point latitude used for envelope extraction")
    parser.add_argument("pm_lon", type=float, help="prime meridian point longitude used for envelope extraction")
    parser.add_argument("timescale", type=str, choices=['daily', 'monthly'], help="timescale of the input data")
    
    parser.add_argument("--uwind", type=str, nargs=2, metavar=('FILE', 'VAR'),
                        help="zonal wind anomaly file and variable")
    parser.add_argument("--vwind", type=str, nargs=2, metavar=('FILE', 'VAR'),
                        help="meridional wind anomaly file and variable")
    parser.add_argument("--sf", type=str, nargs=2, metavar=('FILE', 'VAR'),
                        help="streamfunction anomaly file and variable")
    parser.add_argument("--ofile", type=str, default='test', 
                        help="name of output file (without the file ending - date will be tacked on)")
    
    parser.add_argument("--time", type=str, nargs=3, metavar=('START_DATE', 'END_DATE', 'MONTHS'),
                        help="Time period [default = entire]")

    parser.add_argument("--ticks", type=float, nargs='*', default=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                        help="List of tick marks to appear on the colour bar [default: auto]")
    parser.add_argument("--segments", type=str, nargs='*', default=None,
                        help="List of colours to appear on the colour bar")
    parser.add_argument("--palette", type=str, default='Oranges',
                        help="Colourbar name [default: Organges]")
    parser.add_argument("--projection", type=str, default='cyl', choices=['cyl', 'nsper'],
                        help="Map projection [default: nsper]")
    parser.add_argument("--image_size", type=float, default=9, 
                        help="size of image [default: 9]")
    parser.add_argument("--region", type=str, choices=nio.regions.keys(), default='world-psa',
                        help="name of region to plot [default: world-psa]")

    parser.add_argument("--sf_ticks", type=float, nargs='*', default=[-30, -25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25, 30], 
                        help="list of tick marks for sf contours, or just the number of contour lines")
    parser.add_argument("--search_paths", type=float, nargs=7, default=None,
                        metavar=('NP_LAT', 'NP_LON', 'START_LON', 'END_LON', 'START_LAT', 'END_LAT', 'LAT_STRIDE'),
                        help="draw the search paths for the specified north pole [default: None]")
    
    args = parser.parse_args() 

    main(args)

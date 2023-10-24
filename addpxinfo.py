#!/usr/bin/env python

import pandas as pd
import  numpy as np
import astropy.io.fits as fits
import sys
from lcutils import get_pif_from_file
from badpixel import det_stats

"""
Usage:
addpxinfo.py flares.csv event_dir mask_dir low_e high_e pif_th
"""


column_names = ["scw", "dt0", "t_start_ijd", "t_start", "t_end", "duration", "t_peak", "t_peak_ijd", "mu", "std", "snr_G", "snr_P", "snr_peak_G", "snr_peak_P", "net_cts", "pif_coverage", "good", "det_std"]

fn_template = "{0}/{1}_evts_h.fits.gz"
fn_mask_template = "{0}/{1}_isgri_model.fits.gz"
boundary = 0.01/(24*60*60)


if len(sys.argv) < 7:
	print("Usage:\naddpxinfo.py flares.csv event_dir mask_dir low_e high_e pif_th")
	sys.exit(1)
	
flares_fn = sys.argv[1]
evnt_dir = sys.argv[2]
mask_dir = sys.argv[3]
low_e = np.float64(sys.argv[4])
high_e = np.float64(sys.argv[5])
pif_th = np.float64(sys.argv[6])

fn_flares_new = flares_fn[:-4] + "_b.csv"

flares = pd.read_csv(flares_fn, delimiter="\s+", converters={0: lambda x: str(x)})
print("Before", len(flares.columns.values))
curr_scw = ""
for i in range(len(flares)):
	scw = flares.loc[i, "scw"]
	fn = fn_template.format(evnt_dir, scw)
	fn_mask = fn_mask_template.format(mask_dir, scw)
	flare_start_ijd = flares.loc[i, "t_start_ijd"]
	duration = flares.loc[i, "duration"]
	flare_end_ijd =  flare_start_ijd + duration/(24*60*60)
	if curr_scw != scw:
		pifmask = get_pif_from_file(fn_mask)
		with fits.open(fn) as hdul:
			time = hdul['GNRL-EVTS-LST'].data['TIME']
			energy = hdul['GNRL-EVTS-LST'].data['ENERGY']
			dety = (hdul['GNRL-EVTS-LST'].data['DETY']/4.6).astype(int)
			detz = (hdul['GNRL-EVTS-LST'].data['DETZ']/4.6).astype(int)
			pif = hdul['GNRL-EVTS-LST'].data['PIF_1']
			select_flag = hdul['GNRL-EVTS-LST'].data['EVNT_TYPE'] == 0
		curr_scw = scw

	filtr = (time >= flare_start_ijd - boundary) & \
		(time <= flare_end_ijd + boundary) & \
		(energy >= low_e) & \
		(energy <= high_e) & \
		(select_flag) & \
		(pif >= pif_th)

	dety_target = dety[filtr]
	detz_target = detz[filtr]
	n_photons = np.count_nonzero(filtr)

	H, xedges, yedges = np.histogram2d(detz_target, dety_target, bins=pifmask.shape, range=[[0,133],[0,129]])

	n_photons, nz, npx_pif, expected, c, std, badpx_list = det_stats(H, pifmask, pif_th, show_plots=False, verbose=False)

	print ("{0}: {1}".format(scw, std))
	flares.loc[i, "det_std"] = std

print("After", len(flares.columns.values))
np.savetxt(fn_flares_new, flares.to_numpy(), fmt="%s  %4.2f  %12.8f  %7.2f  %7.2f  %4.2f  %7.2f  %12.8f  %5.2f  %5.2f  %5.1f  %5.1f  %5.1f  %5.1f  %6.1f  %4.3f  %i %5.1f", header=" ".join(flares.columns.values),comments='')

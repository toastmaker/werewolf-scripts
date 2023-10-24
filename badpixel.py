#!/usr/bin/env python
import astropy.io.fits as fits
import numpy as np
import matplotlib.pyplot as plt
from lcutils import get_pif_from_file
import sys

def show_det(det):
	im = plt.imshow(det.T, interpolation=None, vmin=0, vmax=1, origin='lower', extent=[0, 130, 0, 133], cmap=plt.cm.jet)
	plt.xlabel("det y")
	plt.ylabel("det z")
	plt.colorbar(im, orientation="horizontal", pad=0.15)
	
def det_stats(H, pifmask, pif_th, show_plots=True, verbose=True):
	n_photons = np.sum(H.ravel())
	i = pifmask >= pif_th 
	p = H[i].ravel() # pixels above pif threshold
	pnz = np.count_nonzero(p) # pif-pixels with non_zero counts 
	c = p[p > 0].ravel() # non zero counts pixels of illuminated pixels
	
	if show_plots:
		plt.plot(p,"*")
		plt.xlabel('Flattened illuminated pixels')
		plt.ylabel('Counts')
		plt.show()
	npx_pif = np.count_nonzero(i)
	expected = n_photons//npx_pif + 1
	std = np.sqrt(np.sum( (c - expected)**2)/len(c))
	if verbose:
		print("{0:g} photons on {1:g} of {2:g} illuminated pixels".format(n_photons, pnz, npx_pif))
		print("Expected {0:g} photon(s) on pixel\nMean {1:g}\nMax count in pixel {2:g}\nstd {3:g}".format(expected, np.mean(c), np.max(c), std))
	
	badpx_th = expected + 3.*np.sqrt(expected)
	badpx_list = H > badpx_th
	return n_photons, pnz, npx_pif, expected, c, std, badpx_list

def badpixels0(lc, pifmask, pif_th, flare_start_ijd, duration, boundary = 0.01/(24*60*60)):
	time =  lc.arrival_times
	filtr = (time >= flare_start_ijd - boundary) & (time <= flare_end_ijd + boundary)
	dety_target = lc.dety[filtr]
	detz_target = lc.detz[filtr]
	H, xedges, yedges = np.histogram2d(detz_target, dety_target, bins=pifmask.shape, range=[[0,133],[0,129]])	
	n_photons = np.sum(H.ravel())
	i = pifmask >= pif_th 
	p = H[i].ravel() # pixels above pif threshold
	pnz = np.count_nonzero(p) # pif-pixels with non_zero counts 
	c = p[p > 0].ravel() # non zero counts pixels of illuminated pixels
	npx_pif = np.count_nonzero(i)
	expected = n_photons//npx_pif + 1
	std = np.sqrt(np.sum( (c - expected)**2)/len(c))
	badpx_th = expected + 3.*np.sqrt(expected)
	badpx_list = H > badpx_th
	return std

def badpixels(fn, fn_pif, flare_start_ijd, duration, pif_th=0.5, low_e=20, high_e=150, mode="pif", show_plots=True, boundary = 0.01/(24*60*60), verbose=True):
	
	flare_end_ijd =  flare_start_ijd + duration/(24*60*60)
	
	pifmask = get_pif_from_file(fn_pif)
	
	if mode=='raw':
		assert fn_pif != "", "fn_pif must be providd for raw"
		with fits.open(fn) as hdul:
			time = hdul['ISGR-EVTS-ALL'].data['TIME']
			energy = hdul['ISGR-EVTS-ALL'].data['ISGRI_ENERGY']
			dety = hdul['ISGR-EVTS-ALL'].data['DETY'].astype(int)
			detz = hdul['ISGR-EVTS-ALL'].data['DETZ'].astype(int)
			select_flag = hdul['ISGR-EVTS-ALL'].data['SELECT_FLAG'] == 0
			pif = pifmask[detz, dety]
	else:
		with fits.open(fn) as hdul:
			time = hdul['GNRL-EVTS-LST'].data['TIME']
			energy = hdul['GNRL-EVTS-LST'].data['ENERGY']
			dety = (hdul['GNRL-EVTS-LST'].data['DETY']/4.6).astype(int)
			detz = (hdul['GNRL-EVTS-LST'].data['DETZ']/4.6).astype(int)
			pif = hdul['GNRL-EVTS-LST'].data['PIF_1']
			select_flag = hdul['GNRL-EVTS-LST'].data['EVNT_TYPE'] == 0		
	
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
	
	if show_plots:
		# # plot pif mask
		# plt.figure()		
		# show_det(pifmask)
		# plt.title("pif mask)

		# plt.figure()
		# plt.hist(pif,bins=20)
		# plt.title("Distribution of pifs")
		# plt.xlabel("pif")
		
		# plot counts on detector
		plt.figure(figsize=(12,6))
		plt.subplot(121)
		# masking < pif_th to look white
		data_masked = np.ma.masked_where(H.T < 0.001, H.T)
		show_det(data_masked)
		plt.title("{0} on det".format(flare_start_ijd));
		
		# plot counts on detector
		plt.subplot(122)
		pifmask_masked = np.ma.masked_where(pifmask < pif_th, pifmask)
		show_det(pifmask_masked.T)
		plt.xlabel("det y")
		plt.ylabel("det z")
		plt.title("pif mask (> {0})".format(pif_th))
		plt.show()
	n_photons, nz, npx_pif, expected, c, std, badpx_list = det_stats(H, pifmask, pif_th, show_plots=show_plots, verbose=verbose)
	return n_photons, nz, npx_pif, expected, np.max(c), std, badpx_list 


if __name__=="__main__":
	if len(sys.argv) > 1:
		if "-p" in sys.argv:
			sys.argv	.remove("-p")
			show_plots=True
		else:
			show_plots = False
		fn = sys.argv[1]
		fn_pif = sys.argv[2]
		flare_start_ijd = np.float64(sys.argv[3])
		duration = np.float64(sys.argv[4])
		n_photons, nz, npx_pif, expected, m, std, badpx_list = badpixels(fn, fn_pif, flare_start_ijd, duration, show_plots=show_plots)
	else:
		print("Usage: badpixel.py eventlist_fn pif_fn flare_start_ijd duration")

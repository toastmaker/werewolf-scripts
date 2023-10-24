#!/usr/bin/env python

import numpy as np
import astropy.io.fits as fits
import matplotlib.pyplot as plt
from scipy.stats import poisson, norm
from lcutils import make_lightcurve, get_lightcurve, get_lightcurve_raw
from lcutils import plot_zoom, sigma_clipping, moving_average
from lcutils import continuous_regions, merge_regions, get_pif_from_file, find_peaks
from lcutils import sig_G, sig_P
import pandas as pd
import glob
import os
import sys
import getopt
import json
import os.path

from lcutils import par_default

#par_default = { 'low_e': 20., 'high_e': 100., 'pif_threshold':0.5, 'dt': 0.01, 'ignore_pif_weights': True, 'n_binnings': 8, 'prob_th': 1e-6 , 'ignore_gaps': 2}
column_names = ["scw", "dt0", "t_start_ijd", "t_start", "t_end", "duration", "t_peak", "t_peak_ijd", "mu", "std", "snr_G", "snr_P", "snr_peak_G", "snr_peak_P", "net_cts", "pif_coverage", "good"]
SCW_MIN_LENTGH = 1000
patological_scw=['012200730010', '012200750010']	

# Big cycle
def scan_1scw_for_flares(fn, par=par_default, flares=None, verbose=True, check_bad_pixels=False, pif_fn=None):
	if flares is None:
		flares = pd.DataFrame(columns=column_names)
	scw = os.path.basename(fn)[:12]
	if verbose:
		print(f"Processing scw {scw}:", end=" ")
	if scw in patological_scw:
		if verbose:
			print("Blacklisted. Skipping...")
		return flares
	dt0 = par['dt']
			
	try:
		 lc = get_lightcurve(fn, par=par, return_time0=True, return_pif_area=True, return_gti=True)
		 t, r, time0, pif_area, gti = lc.t, lc.r, lc.time0, lc.pif_area, lc.gti 
	except Exception as err:
		if verbose:
			print(err)
			print(f"Getting lc failed. Skipping...")
		return flares
			
	# sanity checks
	if len(t) < SCW_MIN_LENTGH:
		if verbose:
			print("Scw {0} shorter than {1} bins. Skipping...".format(scw, SCW_MIN_LENTGH))
		return flares
	n_gti = np.count_nonzero(gti)
	#r_ = r.copy()
	if n_gti > 0:
		mu, std = sigma_clipping(r)
		print(f"mu = {mu} with all bins")
		mu, std = sigma_clipping(r[gti])
		print(f"mu = {mu} with good bins only")
	#	r_[~gti] = mu
	else:
		mu, std = sigma_clipping(r)

	n_flares_found = 0
	above_across = find_peaks(r, mu, n_binnings=par['n_binnings'], prob_th=par['prob_th'])
	
	if np.any(above_across == True):
		pulses = continuous_regions(above_across)
		merged_pulses = merge_regions(pulses, ignore_gap_size = par['ignore_gaps'])
		
		for start, end in merged_pulses:
			nbins = end-start
			cts = r[start:end]
			i_peak = np.argmax(cts)
			t_peak = t[start:end][i_peak]
			in_gti = np.all(gti[start:end])								
			snr_G = sig_G(cts,mu, std)
			snr_P = sig_P(cts, mu)
			snr_peak_G = sig_G(np.atleast_1d(cts[i_peak]),mu, std)
			snr_peak_P = sig_P(np.atleast_1d(cts[i_peak]),mu)
			ind_end = min(end,t.size-1)				

			flare = pd.DataFrame([{
			"scw": scw,
			"dt0": dt0, 
			"t_start": t[start],
			"t_start_ijd": time0 + t[start]/(24*60*60),
			"t_end": t[ind_end],
			"duration": nbins*dt0,
			"t_peak": t_peak,
			"t_peak_ijd": time0 + t_peak/(24*60*60),
			"mu": mu,
			"std": std,
			"snr_G": snr_G,
			"snr_peak_G": snr_peak_G,
			"snr_P": snr_P,
			"snr_peak_P": snr_peak_P,
			"net_cts": np.sum(cts - mu),
			"pif_coverage": pif_area,
			"good": 1 if in_gti else 0
			}])
			flares = flares.append(flare, ignore_index=True, sort=False)
		n_flares_found = len(merged_pulses)
	if verbose:
		print("ok ({0} flares found)".format(n_flares_found))
	return flares

def scan_scws_for_flares(file_list, par=par_default, flares=None, patological_scw=[], verbose=True):

	if flares is None:
		flares = pd.DataFrame(columns=column_names)

	for fn in file_list:
		flares = scan_1scw_for_flares(fn, par=par, flares=flares, verbose=verbose)

	if verbose:
		print("{0} flares found in total".format(len(flares)))
	return flares

def usage():
	doc = """
-h --help
-d --dir=<dir>
-v --verbose
-p --par=<par.json>
-o --output=<flare_list_output.csv>
-s --sigma-threshold=<sigma_G>
-P --poisson-threshold=<sigma_P>
-w --walltime
-N --nsigma=<nsigma>
-Z --no-zero-mean

Typical usage:

  ffinder2.py -v -o flares/0122_flares_5s.csv -d 0122 -s 5.0 -w
  
  ffinder2.py -v -o flares/012200850010_flares_5s.csv -s 5.0 -P 3.0 0122/012200850010_evts_h.fits.gz
  
"""
	print(doc)
	return None

if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ho:vd:p:s:wP:N:ZF", ["help", "output=","verbose","dir=","par=","sigma-threshold=","walltime","poisson-threshold=","nsigma=", "no-zero-mean"])
	except getopt.GetoptError as err:
		# print help information and exit:
		print(err)  # will print something like "option -a not recognized"
		usage()
		sys.exit(2)

# default settings
	output = None
	verbose = False
	walltime = False
	filelist = args
	sigma_threshold = 0.0
	poisson_threshold = 0.0
	mu_threshold = 0.0
	fn_flares = "flares.csv"
	par = par_default
	new_prob_th = None
	for o, a in opts:
		if o == "-v":
			print("Verbose on")
			verbose = True
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-p", "--par"):
			print("Reading paramaters from file {0}".format(a))
			par = json.load(open(a,'r'))
		elif o in ("-o", "--output"):
			print("Flare will be saved to {0}".format(a))
			fn_flares = a
		elif o in ("-d", "--dir"):
			print("Reading files from directory {0}".format(a))
			directory =  a
			filelist = glob.glob("{0}/*_evts_h.fits.gz".format(directory))
			filelist = sorted(filelist)
		elif o in ("-s","--sigma-threshold"):
			print("Will consider only flares with sigma_G > {0}".format(a))
			sigma_threshold = np.float64(a)
		elif o in ("-P","--poisson-threshold"):
			print("Will consider only flares with sigma_P > {0}".format(a))
			poisson_threshold = np.float64(a)
		elif o in ("-w","--walltime"):
			walltime = True
			import time
			print("Starting wall clock")
			t0 = time.time()
		elif o in ("-N","--nsigma"):
			ns = np.float64(a)
			new_prob_th = norm(0,1).sf(ns)
			print("Setting prob_th equivalent to {0} sigma = {1} (overwrites par file)".format(a,new_prob_th))
		elif o in ("-Z","--no-zero-mean"):
			mu_threshold = 1e-4
		else:
			assert False, "unhandled option"
	#sys.exit(0)
	
	
	if new_prob_th is not None:
		par['prob_th'] = new_prob_th
	
	if verbose:
		print("Parameters of the search:")
		for k, v in par.items():
			print("{0} = {1}".format(k,v))	
	
	flares = scan_scws_for_flares(filelist, par=par, patological_scw=patological_scw, verbose=verbose)
	if walltime:
		t1 = time.time()
		print("Search took {0:.1f} s".format(t1-t0))
	flares.sort_values('t_start_ijd', inplace=True)
	flares_s = flares[ (flares['snr_G']>= sigma_threshold) & (flares['snr_P']>= poisson_threshold) & ( flares['mu'] >= mu_threshold)].copy()
	if verbose:			
		print("{0} flares with snr_G > {1} and snr_P > {2} and mu > {3} found in total".format(len(flares_s), sigma_threshold, poisson_threshold, mu_threshold))

	header = ''
	if not os.path.isfile(fn_flares):
		header = " ".join(flares_s.columns.values)
        
	with open(fn_flares, "ab") as f:
		# f.write(b"\n")
		np.savetxt(f, flares_s.to_numpy(), \
		fmt="%s  %4.2f  %12.8f  %7.2f  %7.2f  %4.2f  %7.2f  %12.8f  %5.2f  %5.2f  %5.1f  %5.1f  %5.1f  %5.1f  %6.1f  %4.3f  %i", header=header,comments='')
	
	# comments = '' to prevent np commenting the header line with #

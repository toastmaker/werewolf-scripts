#!/usr/bin/env python
import numpy as np
import sys
#sys.path.append("/Users/toast/Dropbox/inaf/ffinder/scripts")
from scipy.stats import poisson, norm
from lcutils import *
import pandas as pd
from scipy.special import pdtrc, ndtri, erfinv
from lcutils import par_default
import argparse
import json

def parse():
	parser = argparse.ArgumentParser()
	parser.add_argument("flarefile", type=str,	metavar="inputflares.csv" , help="file with flares")
	parser.add_argument("-o", "--output", type=str, metavar="output.csv",	help="output file with flares")
	parser.add_argument("-p", "--par", type=str, metavar="par.json" , help="search parameter json file")
	parser.add_argument("-P", "--Poisson",	help="use Poisson stat", action="store_true", default=False)
	parser.add_argument("--plot",	help="plot the flare", action="store_true", default=False)
	parser.add_argument("-f", "--eventlist", type=str,	help="eventlist file f-string. \
	May contain {scw}, {rev} wild cards.")
	return parser.parse_args()

def antipif_score(scw, flare, source='SGR1806', fstr='/Users/toast/Dropbox/inaf/arc/{source}/{source}_{scw}_evts_h.fits.gz', Poisson=False):
	rev=scw[0:4]
	fn = fstr.format(source=source, rev=rev, scw=scw)
	lc = get_lightcurve(fn, par=par, return_gti=True, return_time0=True)
	t, r = lc.t, lc.r
	t_ijd = lc.time0 + t/(24.*60.*60.)
	mu = flare['mu'].values[0]
	std = flare['std'].values[0]
	t_s = flare['t_start'].values[0]
	t_s_ijd = flare['t_start_ijd'].values[0]
	t_e = flare['t_end'].values[0]
	tp_ijd = flare['t_peak_ijd'].values[0]
	t_e_ijd = t_s_ijd + (t_e-t_s)/(24*60*60.)
	rng = (t_ijd >= t_s_ijd) & (t_ijd < t_e_ijd)
	mu0, std0 = sigma_clipping(r)
	if Poisson:
		sig = flare['snr_P'].values[0]
		signif = max(sig_P(r[rng], mu), 0)
	else:
		sig = flare['snr_G'].values[0]
		signif = max(sig_G(r[rng], mu, std), 0)
	lc_ap = get_lightcurve(fn, par=par, return_gti=True, time0=lc.time0, antipif=True)
	t_ap, r_ap = lc_ap.t, lc_ap.r
	t_ap_ijd = lc.time0 + t_ap/(24.*60.*60.)
	rng_ap = (t_ap_ijd >= t_s_ijd) & (t_ap_ijd <= t_e_ijd)
	mu_ap, std_ap = sigma_clipping(r_ap)
	net_cts = np.sum(r[rng] - mu)
	net_cts_ap = np.sum(r_ap[rng_ap] - mu_ap)
	net_cts_ratio = (net_cts - net_cts_ap)/(net_cts)
	if Poisson:
		signif_ap = max(sig_P(r_ap[rng_ap], mu_ap), 0)
	else:
		signif_ap = max(sig_G(r_ap[rng_ap], mu_ap, std_ap), 0)
	antipif = signif-signif_ap
	print("{} {:3.1f} {:3.1f} {:3.1f} {:3.1f} {:.1f} {:.1f} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}".format(scw, sig, signif, signif_ap, antipif,\
	 net_cts, net_cts_ap, net_cts_ratio, mu, std, mu_ap, std_ap))
	if args.plot:
		import matplotlib.pyplot as plt
		tp = (tp_ijd-lc.time0)*(24.*60.*60.)
		plt.figure(figsize=(12,12))
		plt.subplot(211)
		plt.step(t,r-mu, color="blue", label="pif", where='post')
		plt.axhline(0., color="black", linestyle=":" )
		plt.step(t_ap, r_ap-mu_ap ,color="red", label="antipif", where='post')
		plt.ylabel("net cts")
		plt.axvline(t_s, color="green", linestyle=":")
		plt.axvline(t_e, color="green", linestyle=":")
		plt.axvline(tp, color="green")
		plt.legend()
		plt.xlim( (t_s - 0.25, t_e + 0.25 ) )
		plt.title(f"{scw} @ {tp_ijd:.8f}")
		
		plt.subplot(212)
		plt.step(t,(r-mu0)/std0, color="blue", label="pif", where='post')
		plt.step(t_ap, (r_ap-mu_ap)/std_ap ,color="red", label="antipif", where='post')
		plt.ylabel("signif")
		plt.axhline(0., color="black", linestyle=":" )
		plt.axvline(t_s, color="green", linestyle=":")
		plt.axvline(t_e, color="green", linestyle=":")
		plt.axvline(tp, color="green")
		plt.legend()
		plt.xlim( (t_s - 0.25, t_e + 0.25 ) )
		plt.show()
	return antipif

if __name__ == "__main__":
    args = parse()
    if args.par is None:
        par = par_default
    else:
        par = json.load(open(args.par,'r'))
	
    flares = pd.read_csv(args.flarefile, delimiter=",", converters={'scw': lambda x: str(x)})
    for i, flare in flares.iterrows():
        scw = flare['scw']
        flares.loc[i, 'antipif'] = antipif_score(scw, flares.loc[[i]], fstr=args.eventlist, Poisson=args.Poisson)
	
    if args.output is not None:
        flares.to_csv(args.output, index=False)

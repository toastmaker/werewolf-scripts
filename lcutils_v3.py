import numpy as np
import astropy.io.fits as fits
import matplotlib.pyplot as plt
from scipy.stats import poisson, norm
from scipy.special import pdtrc, ndtri, erfinv
# par_default = {'low_e': 20., 'high_e': 200., 'pif_threshold':0.5, 'dt':0.5 }

par_default = { 'low_e': 20., 'high_e': 100., 'pif_threshold':0.5, 'dt': 0.01, 'ignore_pif_weights': True, 'n_binnings': 6, 'prob_th': 1e-6, 'ignore_gaps': 3, 'ns': None, 'prob_false': 1e-2 }

class Lightcurve():
	def __init__(self):
		pass

def sig_G(r, b, b_std):
	"""Gaussian significance of the flare segment"""
	nbins = len(r)
	if np.isscalar(b):
		return np.sum(r-b)/(np.sqrt(nbins)*b_std)
	else:
		return np.sum(r-b)/ np.sqrt( np.sum(b_std**2))

def sig_P(r, b):
	"""Poisson significance of the flare segment"""
	nbins  = len(r)
	c = np.sum(r)
	if np.isscalar(b):
		true_bg = b*nbins
	else:
		true_bg = np.sum(b)
	pval = pdtrc(c, true_bg) # poisson pdf
	#return np.sqrt(2)*erfinv(1-2*pval)
	sig = -ndtri(pval) # equivalent to np.sqrt(2)*erfinv(1-2*pvalue)
	if sig == np.inf:
		return sig_G(r, b, np.sqrt(b)) # to have something for huge significances to return
	else:
		return sig


def get_off_per_module(fn, tstart, dt, tend=None, tseg=None, time0 = None, w=5):
	"""
	create a 0|1 binary "light curve" 
	"""
	with fits.open(fn) as hdu:
		time = hdu['ISGR-EVTS-ALL'].data['TIME']
		dety = hdu['ISGR-EVTS-ALL'].data['DETY'].astype(int)
		detz = hdu['ISGR-EVTS-ALL'].data['DETZ'].astype(int)

		sortind = np.argsort(time)
		time = time[sortind]
		dety = dety[sortind]
		detz = detz[sortind]
		sec_in_day = 24*60*60
		if time0 is None:
			time0 = time[0]
		arr_times = (time - time0)*sec_in_day

		lc = Lightcurve()
		module =  (detz/34)//1 + ( (dety/65)//1)*4
		for m in range(8):
			t_,r_ = make_lightcurve(arr_times[module==m], tstart=tstart, tend=tend, dt=dt, use_hist=True)
			avg_ = moving_average(r_, w=w).copy()
			setattr(lc, 'nonzero%i'%m, (avg_ > 0))	
		lc.t = t_.copy()
		return lc	

def sigma_clipping_per_module(lc, off, mode="gaussian", gti=[], ignore_gap_size=50):
	# mode=gaussian | poisson
	# mu, std can vary bin to bin, this function return arrays

	mu_all = np.zeros( (8,len(lc.t)) )
	std_all = np.zeros( (8,len(lc.t)) )

	for m in range(8):
		lc_ = getattr(lc, "r%i"%m)
		dt2 = (off.t[1]-off.t[0])/2.
		nonz = getattr(off, "nonzero%i"%m).copy()
		crm = merge_regions(continuous_regions(nonz), ignore_gap_size=ignore_gap_size)
		nonz_ = np.zeros_like(lc.t, dtype=bool)
		for s,e in crm:
			e = min(e, len(off.t)-1)
			i = (lc.t >= off.t[s]-dt2 ) & (lc.t <= off.t[e]+2*dt2) # +dt2
			if len(gti)>0:
				nonz_[ i & gti ] = True # & gti 
			else:
				nonz_[ i ] = True
		
		mu_all[m,nonz_ & gti], std_all[m,nonz_ & gti] = sigma_clipping(lc_[nonz_ & gti], mode=mode)
	mu = np.sum(mu_all, axis=0)
	std = np.sqrt(np.sum(std_all**2, axis=0))
	return mu, std

def find_peaks_old(r, threshold, n_binnings=8):
	above = np.zeros((n_binnings, len(r)), dtype=bool)

	for i in range(n_binnings):
		width = 2**i
		r_ = width*moving_average(r,w=width)
		above[i,:] = (r_ > threshold[i]) & (r > 0)

	above_across = np.logical_or.reduce(above[:,:], axis=0)
	return above_across

def find_peaks_np(r, mu, n_binnings=8, prob_th=1e-5, false_rate=None, ns=None):
	if ns is not None:
		prob_th = norm(0,1).sf(ns)
	
	if false_rate is not None:
		prob_th = false_rate/r.size
	#above = np.zeros((n_binnings, len(r)), dtype=bool)
	width = 2**np.arange(n_binnings)[np.newaxis,:]
	threshold = poisson(width*mu).isf(prob_th)
	k = np.ones(width)/width
	r_ = width*np.convolve(r, k, 'same')
	above = r_ > threshold & r >= mu
	above_across = np.logical_or.reduce(above[:,:], axis=0)
	return above_across

def find_peaks_G(r, mu, std, n_binnings=8, prob_th=1e-5, false_rate=None, ns=None):

	if ns is not None:
		prob_th = norm(0,1).sf(ns)

	if false_rate is not None:
		prob_th = false_rate/r.size

	above = np.zeros((n_binnings, len(r)), dtype=bool)
	for i in range(n_binnings):
		width = 2**i
		threshold = norm( width*mu, std/np.sqrt(width) ).isf(prob_th)
		r_ = width*moving_average(r,w=width)
		above[i,:] = (r_ > threshold) & (r >= mu) # & (r > mu) # & (r > 0)

	above_across = np.logical_or.reduce(above[:,:], axis=0)
	return above_across



def find_peaks_variable_mu(r, mu, n_binnings=8, prob_th=1e-5, false_rate=None, ns=None):

	if ns is not None:
		prob_th = norm(0,1).sf(ns)

	if false_rate is not None:
		prob_th = false_rate/r.size

	above = np.zeros((n_binnings, len(r)), dtype=bool)
	for i in range(n_binnings):
		width = 2**i
		mu_ = width*moving_average(mu,w=width)
		threshold = poisson(mu_).isf(prob_th)
		r_ = width*moving_average(r,w=width)
		above[i,:] = (r_ > threshold) & (r >= mu) # & (r > mu) # & (r > 0)

	above_across = np.logical_or.reduce(above[:,:], axis=0)
	return above_across


def find_peaks(r, mu, n_binnings=8, prob_th=1e-5, false_rate=None, ns=None):
	
	if ns is not None:
		prob_th = norm(0,1).sf(ns)

	if false_rate is not None:
		prob_th = false_rate/r.size

	above = np.zeros((n_binnings, len(r)), dtype=bool)
	for i in range(n_binnings):
		width = 2**i
		threshold = poisson(width*mu).isf(prob_th)
		r_ = width*moving_average(r,w=width)
		above[i,:] = (r_ > threshold) & (r >= mu) # & (r > mu) # & (r > 0)

	above_across = np.logical_or.reduce(above[:,:], axis=0)
	return above_across

def get_pif_from_file(fn, ext='ISGR-PIF.-SHD'):
	with fits.open(fn) as hdu:
		pif = hdu[ext].data
		return pif.astype(float)

def continuous_regions(mask):
	d = np.diff(mask)
	idx, = d.nonzero()
	# We need to start things after the change in mask. Therefore,
	# we'll shift the index by 1 to the right.
	idx += 1

	if mask[0]:
		# If the start of mask is True prepend a 0
		idx = np.r_[0, idx]

	if mask[-1]:
		# If the end of mask is True, append the length of the array
		idx = np.r_[idx, mask.size]

	# Reshape the result into two columns
	idx.shape = (-1,2)
	return idx

def merge_regions(temp_tuple, ignore_gap_size = 0):
	temp_tuple.sort(axis=0) # key=lambda interval: interval[0])
	merged = [temp_tuple[0]]
	for current in temp_tuple:
		previous = merged[-1]
		if current[0]  <= previous[1] + ignore_gap_size:
			previous[1] = max(previous[1], current[1])
		else:
			merged.append(current)
	return np.array(merged)

def moving_average(x, w=1):
	return np.convolve(x, np.ones(w)/w, 'same')

def poiss_ns_threshold(mu, ns):
	"""Returns Poisson(mu) count threshold equivalent to ns sigma
	"""
	normal = norm(0,1)
	prob_th = normal.sf(ns)
	pois = poisson(mu)
	th = pois.isf(prob_th)
	return th

def sigma_clipping(r, niter=3, ns=3, mode="gaussian"):
	x_ = r.copy() 
	for i in range(niter):
		if mode=="gaussian":
			mu, std = np.mean(x_), np.std(x_)
			# if ns*std < 1:
			# 	# if there is so few counts that it would clip everything, forget about clipping
			#	return mu, std 
			x_ = x_[ np.abs(x_ - mu) <= ns*std ]
		else:
			mu = np.mean(x_)
			std = np.sqrt(mu)
			th = poiss_ns_threshold(mu, ns)
			x_ = x_[ x_ <= th ]
	if mode=="gaussian":	
		mu, std = np.mean(x_), np.std(x_)
	else:
		mu = np.mean(x_)
		std = np.sqrt(mu)
	if mu < 1e-7:
		# forget about clipping when there is so few counts
		mu, std = np.mean(r), np.std(r)
	return mu, std

def GTI_filtr(t, gti):
	gti_filtr = np.zeros_like(t, dtype=bool)
	for start, end in gti:
		gti_filtr[ (t >= start) & (t <= end)] = True
	return gti_filtr

def get_GTI(fn, ext='GNRL-EVTS-GTI'):
	hdu = fits.open(fn)
	gti_start = hdu[ext].data['START']
	gti_end = hdu[ext].data['STOP']
	return np.column_stack([gti_start,gti_end])

def make_lightcurve(toa, dt, tseg=None, tstart=None, tend=None, weights=None, use_hist=False, keepLastBin=False):
	"""
	toa ... time of arrival
	tseg ... length
	tstart ... start lc from time

	weights ... pif values for the histogram
	"""
	toa = np.sort(np.asarray(toa))
	if tstart is None:
		tstart = toa[0]
	if tseg is None:
		tseg = toa[-1] - tstart
#	print("tstart: " + str(tstart))
#	print("tend: " + str(toa[-1]))
#	print("tseg: " + str(tseg))
	nbins = np.int64(tseg / dt)
#	print("#bins:  " + str(nbins))
	if tend is None:
		tend = tstart + nbins * dt
	good = (tstart <= toa) & (toa <= tend)
	
	if weights is None:
		w = None
	else:
		w = weights[good]
	
	if not use_hist:
		binned_toas = ((toa[good] - tstart) // dt).astype(np.int64)
		counts = np.bincount(binned_toas, minlength=nbins, weights=w)
		times = tstart + np.arange(0.5, 0.5 + len(counts)) * dt
	else:
		histbins = np.arange(tstart, tend + dt, dt)
		counts, histbins = np.histogram(toa[good], bins=histbins, weights=w)
		times = histbins[:-1] + 0.5 * dt
	if keepLastBin:
		return times, counts
	else:
		return times[:-1], counts[:-1]
	
	
def plot_zoom(t,r, t1=None, t2=None):
	"""
	"""
	if t1 is None:
		t1 = np.min(t)
	if t2 is None:
		t2 = np.max(t)
	zoom = (t > t1) & (t < t2)
	plt.plot(t[zoom],r[zoom])


def plot_all(t,r,peaks, mu,std,threshold, gti=None, alpha=0.3):
	plot_zoom(t,r)
	if np.isscalar(mu):
		mu = mu*np.ones_like(t)
		std = std*np.ones_like(t)
	if np.isscalar(threshold):
		threshold = threshold*np.ones_like(t)
	plt.plot(t, mu, color="green")
	plt.plot(t, threshold, linestyle="--", color="red")
	plt.plot(t,mu-3*std, linestyle=":", color="green")
	plt.plot(t,mu+3*std, linestyle=":", color="green")
#	plt.axhline(y=mu, color="green")
#	plt.axhline(y=threshold, linestyle="--", color="red")
#	plt.axhline(y=mu-3*std, linestyle=":", color="green")
#	plt.axhline(y=mu+3*std, linestyle=":",color="green")

#	print("Found", len(peaks), "bins above threshold")

	for p in peaks:
		plt.axvline(x=p, color='red',alpha=alpha)

	if gti is not None:
		bad_time_interval = continuous_regions(np.logical_not(gti))
		for bad_start, bad_end in bad_time_interval:
			plt.axvspan(t[bad_start], t[bad_end-1], alpha=0.1, color='grey')
	
def get_arrival_times(eventlist_fn, par=par_default, gti=None, raw=False, time0=None, return_time0=False):
	
	if raw:
		hdu = fits.open(eventlist_fn)
		time = hdu['ISGR-EVTS-ALL'].data['TIME']
		energy = hdu['ISGR-EVTS-ALL'].data['ISGRI_ENERGY']
		sortind = np.argsort(time)
		time = time[sortind]

	else:
		hdu = fits.open(eventlist_fn)
		#	dety = hdu['GNRL-EVTS-LST'].data['DETY']
		#	detz = hdu['GNRL-EVTS-LST'].data['DETZ']
		energy = hdu['GNRL-EVTS-LST'].data['ENERGY']
		time = hdu['GNRL-EVTS-LST'].data['TIME']
		pif = hdu['GNRL-EVTS-LST'].data['PIF_1']
		evnt_type = hdu['GNRL-EVTS-LST'].data['EVNT_TYPE']
	
		sortind = np.argsort(time)
		time = time[sortind]
		#	dety = dety[sortind]
		#	detz = detz[sortind]
		energy = energy[sortind]
		pif = pif[sortind]
		evnt_type = evnt_type[sortind]

	sec_in_day = 24*60*60
	if time0 is None:
		time0 = time[0]
	arr_times = (time - time0)*sec_in_day
			
	if gti:
		good = np.zeros_like(arr_times, dtype=np.bool)
		for gti_start, gti_end in gti:
			ind = (arr_times >= gti_start) & (arr_times <= gti_end)
			good[ind] = True
	else:
		# take all
		good = np.ones_like(arr_times, dtype=np.bool)
		# good = ((arr_times >= arr_times[0]) & (arr_times <= arr_times[-1]) ) 
		
	select_flag = evnt_type == 0
	filtr = (energy > par['low_e']) & (energy < par['high_e']) \
			& good & select_flag
	
	if not raw:
		filtr = filtr & (pif > par['pif_threshold'])
	
	arr_times = arr_times[filtr]
	
	if not raw:
		weights = pif[filtr]
	else:
		weights = np.ones_like(arr_times)
	if return_time0:
		return arr_times, weights, time0
	else:
		return arr_times, weights



def get_lightcurve_raw(eventlist_fn, par=par_default, time0 = None, pifmask=None, \
                       return_time0=False, \
                       return_pif_area=False, \
                       return_gti=False, \
                       per_module=False):
	
	with fits.open(eventlist_fn) as hdu:
	
		time = hdu['ISGR-EVTS-ALL'].data['TIME']
		energy = hdu['ISGR-EVTS-ALL'].data['ISGRI_ENERGY']
		dety = hdu['ISGR-EVTS-ALL'].data['DETY'].astype(int)
		detz = hdu['ISGR-EVTS-ALL'].data['DETZ'].astype(int)
		select_flag = hdu['ISGR-EVTS-ALL'].data['SELECT_FLAG']
	
		sortind = np.argsort(time)
		time = time[sortind]
		energy = energy[sortind]
		dety = dety[sortind]
		detz = detz[sortind]
		select_flag = select_flag[sortind]
		sec_in_day = 24*60*60
		if time0 is None:
			time0 = time[0]
		arr_times = (time - time0)*sec_in_day
			
		good = ((arr_times >= arr_times[0]) & (arr_times <= arr_times[-1]) ) # prep for GTI
			
		filtr = (energy >= par['low_e']) & (energy <= par['high_e']) \
				& good & (select_flag == 0)
			
		if (pifmask is not None):
			pif = pifmask[detz, dety]
			filtr = filtr & (pif >= par['pif_threshold'])
			pif = pif[filtr]
		arr_times = arr_times[filtr]
		tstart = arr_times[0]
		dety = dety[filtr]
		detz = detz[filtr]
	
		if (pifmask is None) or (par['ignore_pif_weights']):
			t,r = make_lightcurve(arr_times, dt=par['dt'], use_hist=True)
		else:
			t,r = make_lightcurve(arr_times, dt=par['dt'], use_hist=True, weights=pif)
	
		lc = Lightcurve()
		lc.t = t
		lc.r = r
		
		if per_module:
			module =  (detz/34)//1 + ( (dety/65)//1)*4
			for m in range(8):
				if (par['ignore_pif_weights']):
					
					t_,r_ = make_lightcurve(arr_times[module==m], tstart=tstart, dt=par['dt'], use_hist=True)
				else:
					t_,r_ = make_lightcurve(arr_times[module==m], tstart=tstart ,dt=par['dt'], use_hist=True, weights=pif[module==m])
				setattr(lc, 'r%i'%m, r_)		
		
		if return_time0:
			lc.time0 = time0
		if return_pif_area:
			pif_area = ( np.max(detz) - np.min(detz)) * (np.max(dety) - np.min(dety)) / (134.*130.)
			# detector pixels 134x130
			lc.pif_area = pif_area
			
		if return_gti:
			gti_start = hdu['IBIS-GNRL-GTI'].data['START']
			gti_end   = hdu['IBIS-GNRL-GTI'].data['STOP']
			gti = np.column_stack([gti_start,gti_end])
			gti = (gti-time0)*sec_in_day
			gti_filtr = np.zeros_like(t, dtype=bool)
			for start, end in gti:
				gti_filtr[ (t >= start-par['dt']) & (t <= end+par['dt'])] = True
			lc.gti =  gti_filtr
		return lc
				
def get_lightcurve(eventlist_fn, par=par_default, time0 = None, \
                   return_time0=False, \
                   return_pif_area=False, \
                   return_gti=False, \
                   per_module=False, \
                   return_arrival_times=False, \
                   return_detyz=False):
	# raw event list in extension ISGR-EVTS-ALL, pif in GNRL-EVTS-LST
	
	with fits.open(eventlist_fn) as hdu:
	
		if return_pif_area or per_module or return_detyz:
			dety = hdu['GNRL-EVTS-LST'].data['DETY']
			detz = hdu['GNRL-EVTS-LST'].data['DETZ']
		
		energy = hdu['GNRL-EVTS-LST'].data['ENERGY']
		time = hdu['GNRL-EVTS-LST'].data['TIME']
		pif = hdu['GNRL-EVTS-LST'].data['PIF_1']
		evnt_type = hdu['GNRL-EVTS-LST'].data['EVNT_TYPE']
		
		sortind = np.argsort(time)
		time = time[sortind]
		energy = energy[sortind]
		pif = pif[sortind]
		evnt_type = evnt_type[sortind]
		if return_pif_area or per_module  or return_detyz:
			dety = dety[sortind]
			detz = detz[sortind]
	
		sec_in_day = 24*60*60
		if time0 is None:
			time0 = time[0]
			
		# good = ((arr_times >= arr_times[0]) & (arr_times <= arr_times[-1]) ) 
		
		select_flag = evnt_type == 0
		
		filtr = (energy >= par['low_e']) & (energy <= par['high_e']) \
		        & (pif >= par['pif_threshold']) & select_flag
		        
		arr_times = time[filtr]
		lc = Lightcurve()
		if return_arrival_times:
			lc.arr = arr_times
		arr_times = (arr_times - time0)*sec_in_day

		pif = pif[filtr]
		if return_pif_area or per_module or return_detyz:
			dety = dety[filtr]
			detz = detz[filtr]

		if return_detyz:
			lc.dety = dety
			lc.detz = detz


		tstart = arr_times[0] # hope they are sorted already, it's faster than arr_times.min()
		tseg = arr_times[-1]-tstart
		if (par['ignore_pif_weights']):
			t,r = make_lightcurve(arr_times, tstart=tstart, tseg=tseg, dt=par['dt'], use_hist=True)
		else:
			t,r = make_lightcurve(arr_times, tstart=tstart, tseg=tseg, dt=par['dt'], use_hist=True, weights=pif)
		
		lc.t = t
		lc.r = r
		
		if per_module:
			module =  (detz/4.6/34)//1 + ( (dety/4.6/65)//1)*4
			for m in range(8):
				if (par['ignore_pif_weights']):
					
					t_,r_ = make_lightcurve(arr_times[module==m], tstart=tstart, tseg=tseg, dt=par['dt'], use_hist=True)
				else:
					t_,r_ = make_lightcurve(arr_times[module==m], tstart=tstart, tseg=tseg, dt=par['dt'], use_hist=True, weights=pif[module==m])
				setattr(lc, 'r%i'%m, r_.copy())
		
		if return_time0:
			lc.time0 = time0
			
		if return_pif_area:
			pif_area = (np.max(detz) - np.min(detz)) * (np.max(dety) - np.min(dety)) /(134*4.6*130*4.6)
			# detector size in mm 134*4.6 x 130*4.6
			lc.pif_area = pif_area
			
		if return_gti:
			gti_start = hdu['GNRL-EVTS-GTI'].data['START']
			gti_end   = hdu['GNRL-EVTS-GTI'].data['STOP']
			gti = np.column_stack([gti_start,gti_end])
			gti = (gti-time0)*sec_in_day
			gti_filtr = np.zeros_like(t, dtype=bool)
			for start, end in gti:
				gti_filtr[ (t >= start -par['dt']) & (t <= end+par['dt'])] = True # +/i par['dt']/2. removed
			lc.gti =  gti_filtr
		
		return lc
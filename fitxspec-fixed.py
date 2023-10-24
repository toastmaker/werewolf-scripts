from xspec import *
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import sys

#fn = sys.argv[1] # fn="isgri_spectrum.fits"

i = int(sys.argv[1])
scw = str(sys.argv[2])
fn = "/home/topinka/spectra/SGR1806_bright/spe_SGR_%04i/obs/spe/scw/%s.001/isgri_spectrum.fits"%(i,scw)

s = Spectrum(fn)

# test last bin
Plot.device="/null"
Plot.xAxis = "keV"
Plot("ldata")
r=Plot.y()
r_err=Plot.yErr()
n = len(r)
print(r[n-1], r_err[n-1])
if (r[n-1] - r_err[n-1]) < 1:
	print("ignoring last bin")
	s.ignore("15")

# s.ignore("15")
#Plot.device = "/xs"
Plot.device="/null"
Plot.xAxis = "keV"
Plot.xLog = True
Plot.yLog = True
m = Model("cutoff")
m.cutoffpl.PhoIndex.values = 0.5
m.cutoffpl.PhoIndex.frozen = True
Fit.nIterations = 300
Fit.statMethod = "chi"
Fit.query = "yes"
Fit.perform()
E0 = m.cutoffpl.HighECut.values[0]
E0_err = m.cutoffpl.HighECut.sigma
alpha = m.cutoffpl.PhoIndex.values[0]
alpha_err = m.cutoffpl.PhoIndex.sigma
norm = m.cutoffpl.norm.values[0]
norm_err = m.cutoffpl.norm.sigma

Plot("ldata")

chi2 = Fit.statistic
dof = Fit.dof
redchi2 = chi2/dof
nullhyp = Fit.nullhyp

# fluxes
fluxes = {} # ergs/cm^2/s
fluxes_ph = {} # photons 
for low, high in [ (20,40), (40, 100), (20, 100) ]:
    AllModels.calcFlux("%i %i"%(low, high))
    fluxes["%i_%i"%(low, high)] = s.flux[0]
    fluxes_ph["%i_%i"%(low,high)] = s.flux[3]

en=Plot.x()
r=Plot.y()
en_err=Plot.xErr()
r_err=Plot.yErr()
mo=Plot.model()

f = plt.figure()
plt.step(en,mo,color="red", where='mid')
plt.scatter(en, r)
plt.errorbar(en, r ,xerr=en_err, yerr=r_err, fmt="none")
plt.xlabel("Energy [keV]")
plt.ylabel(r"counts/cm$^2$/s/keV")
plt.title("SGR flare %i"%i)
plt.xscale('log')
plt.yscale('log')

g = plt.gca()
g.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
g.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
g.xaxis.set_minor_formatter(StrMethodFormatter('{x:,.0f}'))
plt.savefig("spectrum-cutoffpl-fixed_%04i.pdf"%i)
plt.close(f)

print("%04i"%i, E0, E0_err, alpha, alpha_err, norm, norm_err, chi2, dof, redchi2, nullhyp, fluxes['20_100'],fluxes_ph['20_100'], fluxes['20_40'], fluxes_ph['20_40'], fluxes['40_100'], fluxes_ph['40_100'])



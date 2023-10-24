#!/usr/bin/env python

import numpy as np
import astropy.io.fits as fits
import sys

fn = sys.argv[1] # '/home/topinka/SGR1806/lists/SGR1806_fov.scw'
TL = 0.
print ("scw centre_ijd elapsed")
for line in open(fn, "r"):
    scw = line.strip()
    rev = scw[0:4]
    try:
      isgri = "/storage/topinka/SGR1806/out/%s/%s_evts_h.fits.gz"%(rev, scw)
      hdu = fits.open(isgri)
      elapsed = np.float(hdu[1].header['TELAPSE'])
      first = hdu[1].header['TFIRST']
      last = hdu[1].header['TLAST']
      ijd = (last+first)/2.
      print(scw, ijd, elapsed)
    except:
        elapsed = 0.
    TL += elapsed
print("#", TL)
print("#", TL/1e6, "Ms")
print("#", TL/(365*24*60*60.), "years")


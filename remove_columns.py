#!/usr/bin/env python
import astropy.io.fits as fits
from astropy.table import Table
import sys

ext = 2
if len(sys.argv) < 3:
    sys.exit(0)
fn = sys.argv[1]

hdul=fits.open(fn)
data = Table.read(fn, format="fits", hdu=ext)
data.remove_columns([*sys.argv[2:]])
hdul[ext].data = data.as_array()
hdul.writeto(fn, overwrite=True)



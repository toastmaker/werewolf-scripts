#!/usr/bin/env python
import astropy.io.fits as fits
import sys
import os

def update_header1(origf, rawf, newf, extorig=2, extraw=3):
    """
    modify origf with spacecraft position from rawf 
    """
    with fits.open(rawf) as rawl:
        with fits.open(origf, mode='update') as hdul:
            hdr = hdul[extorig].header
            hdr['RA_SCX'] = rawl[extraw].header['RA_SCX']
            hdr['RA_SCZ'] = rawl[extraw].header['RA_SCZ']
            hdr['DEC_SCX'] = rawl[extraw].header['DEC_SCX']
            hdr['DEC_SCZ'] = rawl[extraw].header['DEC_SCZ']
            hdul.writeto(newf, overwrite=True)

if __name__=="__main__":
    origf = sys.argv[1]
    rawf = sys.argv[2]
    newf = sys.argv[3]
    print("Updating {0} header with {1} telemetry".format(origf, rawf))
    update_header1(origf, rawf, newf)

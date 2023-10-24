#!/usr/bin/env python
import astropy.io.fits as fits
import sys

def update_src_cat(src_name, src_ra, src_dec, new_fn, \
                  fn_template = "/home/topinka/catalogs/FRBM81_ii_specat.fits"):
	with fits.open(fn_template) as hdu:
		source = hdu['ISGR-SRCL-RES'].data[0]
		source['NAME'] = src_name
		source['RA_OBJ'], source['DEC_OBJ'] = src_ra, src_dec
		source['RA_FIN'], source['DEC_FIN'] = src_ra, src_dec
		print("Writing source name {} and coordinates {:.4f}, {:.4f} to {}".format(source['NAME'], source['RA_FIN'], source['DEC_FIN'], new_fn))
		hdu.writeto(new_fn, overwrite=True)

if __name__ == "__main__":
	try:
		src_name, src_ra, src_dec, new_fn = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
	except:
		print("Usage: ", sys.argv[0], "src_name src_ra src_dec newfile.fits")
		exit(1)
	update_src_cat(src_name, src_ra, src_dec, new_fn)

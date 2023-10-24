#!/usr/bin/env python3
import sqlite3
import astropy.io.fits as fits
import sys

def post_row(conn, tablename, rec):
    keys = ','.join(rec.keys())
    question_marks = ','.join(list('?'*len(rec)))
    values = tuple(rec.values())
    conn.execute('INSERT OR REPLACE INTO '+tablename+' ('+keys+') VALUES ('+question_marks+')', values)


db_file = "scwcheck.db"
table_name = 'headers'
fn = sys.argv[1]
if len(sys.argv) > 2:
  db_file = sys.argv[2]

print("Opening {} ...".format(fn))
hdu = fits.open(fn)
h = hdu['ISGR-EVTS-ALL'].header
keys2save = ['SWID','SW_TYPE','NAXIS2', 'TSTART','TSTOP','TELAPSE','RA_SCX','DEC_SCX',
            'RA_SCZ', 'DEC_SCZ', 'L2_SCX', 'B2_SCX', 'TIMECORR', 'TIMEREF', 'TIMESYS', 'SWBOUND',
            'TFIRST', 'TLAST']

print("Getting keywords...")
d = {}
for k in keys2save:
    d[k] = h.get(k,None)

print("Udpating sqlite3 table...")
conn = sqlite3.connect(db_file)
post_row(conn, table_name, d)
conn.commit()
conn.close()


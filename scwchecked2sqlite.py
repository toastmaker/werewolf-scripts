#!/usr/bin/env python
import sys, os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
import getopt

db_file = "scwcheck.db"

def mysql_replace_into(table, conn, keys, data_iter):

	@compiles(Insert)
	def replace_string(insert, compiler, **kw):
		s = compiler.visit_insert(insert, **kw)
		s = s.replace("INSERT INTO", "INSERT OR IGNORE INTO") # REPLACE
		return s

	data = [dict(zip(keys, row)) for row in data_iter]

	conn.execute(table.table.insert(replace_string=""), data)

def create_db(db_file):
	conn = sqlite3.connect(db_file)
	c = conn.cursor() # AUTOINCREMENT
	c.execute('''CREATE TABLE scws
			  ( id INTEGER PRIMARY KEY ,
			  ScW VARCHAR(12) UNIQUE,
			  TSTART REAL,
			  TSTOP REAL,
			  RA_X REAL,
			  DEC_X REAL,
			  RA_Z REAL,
			  DEC_Z REAL,
			  duration REAL,
			  expos REAL,
			  off REAL,
			  modules_Toff1 REAL,
			  modules_Toff2 REAL,
			  modules_Toff3 REAL,
			  modules_Toff4 REAL,
			  modules_Toff5 REAL,
			  modules_Toff6 REAL,
			  modules_Toff7 REAL,
			  modules_Toff8 REAL,
			  corrected_rates1 REAL,
			  corrected_rates2 REAL,
			  corrected_rates3 REAL,
			  corrected_rates4 REAL,
			  corrected_rates5 REAL,
			  corrected_rates6 REAL,
			  corrected_rates7 REAL,
			  corrected_rates8 REAL,
			  stdv REAL,
			  chired REAL,
			  dd0 REAL,
			  dd1 REAL,
			  NCTS BIGINT);''')
	conn.commit()
	conn.close()
	return None


# parse command line

try:
	opts, args = getopt.getopt(sys.argv[1:], "D:qh", ["database=","quiet", "help"])
except getopt.GetoptError as err:
	# print help information and exit:
	print(err)  # will print something like "option -a not recognized"
	print(sys.argv[0], "[-D | --database= sqlite3.db ] [ -q | --quiet ] input_table.txt")
	sys.exit(2)

quiet = False
for o, a in opts:
	if o in ("-h", "--help"):
		print("Usage: ", sys.argv[0], "[-D | --database=sqlite3.db ] [ -q | --quiet ] [ -h | --help ] input_table.txt")
		sys.exit(0)
	elif o in ("-D", "--database"):
		db_file = a
	elif o in ("-q", "--quiet"):
		quiet = True
	else:
		assert False, "unhandled option"
assert len(args) == 1, "1 input file needed!"

fn = args[0]
print ("input fn = ", fn)
print("db_file: ", db_file)

# sys.exit(0)
# read file
cols = "ScW TSTART TSTOP RA_X DEC_X RA_Z DEC_Z YANG ZANG duration expos off modules_Toff1 modules_Toff2 modules_Toff3 modules_Toff4 modules_Toff5 modules_Toff6 modules_Toff7 modules_Toff8 corrected_rates1 corrected_rates2 corrected_rates3 corrected_rates4 corrected_rates5 corrected_rates6 corrected_rates7 corrected_rates8 stdv chired dd0 dd1 NCTS".split()
pd_scwcheck = pd.read_csv(fn, delimiter="\s+", comment="#", names=cols)
if pd_scwcheck['ScW'].apply(lambda x: str(x)).str.contains("0010$").all():
	pd_scwcheck['ScW'] = pd_scwcheck['ScW'].apply(lambda x: str(x).zfill(12))
else:
	pd_scwcheck['ScW'] = pd_scwcheck['ScW'].apply(lambda x: str(x).zfill(8) + "0010")
# pd_scwcheck.set_index('ScW', inplace=True)
pd_scwcheck.drop(pd_scwcheck[pd_scwcheck.RA_X < -900].index, inplace=True)
pd_scwcheck.drop(['YANG', 'ZANG'], axis=1, inplace=True)

# if not exists create the sqlite db file
if not os.path.exists(db_file):
	print("DB not exists, let's create it!")
	create_db(db_file)
else:
	print("DB exists. No need it to create it.")

# pour df to sqlite
# conn = sqlite3.connect('scwcheck.db')
engine = create_engine('sqlite:///{}'.format(db_file), echo=True)
conn = engine.connect()

pd_scwcheck.to_sql(name='scws', con=conn,
#				   index_label='ScW',
				   if_exists='append', 
                   index=False,
				   method=mysql_replace_into)
conn.close()

# sanity check, print the content
if not quiet:
	conn = sqlite3.connect(db_file)
	SELECT_STR = '''SELECT * FROM scws'''  # LIMIT 3
	cursor = conn.execute(SELECT_STR)
	n = len(list(cursor))
	for row in cursor:
		print(row)
	conn.close()
	print("{} recrods in the db".format(n))

#!/bin/bash

# src="PSR1259"
src=$1

cmd="/home/topinka/scripts/addpxinfo.py"
eventdir="/storage/topinka/${src}/out"
maskdir="/storage/topinka/${src}/masks"
cd ${HOME}/${src}/flares
for f in `ls ????_flares_6s.csv`; do
  scw="${f:0:4}"
  ${cmd} $f "${eventdir}/${scw}" "${maskdir}/${scw}" 20. 100. 0.5
done

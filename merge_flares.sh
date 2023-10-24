#!/bin/bash
CONFIG=$1
[ "x${CONFIG}" = "x" ] && echo -e "Define config.json argument!\nUsage: ff_per_rev.sh config.json" && exit 1

SOURCE=`jq -r '.SOURCE' < ${CONFIG}`
SIGMA=6

cd ${HOME}/${SOURCE}/flares

for rev in `ls *.csv | awk '{print substr($1,1,4)}' | uniq`; do

  FLARES_REV_FILE="${HOME}/${SOURCE}/flares/${rev}_flares_${SIGMA}s.csv"
  if [ ! -f "${FLARES_REV_FILE}" ]; then
      echo "${FLARES_REV_FILE} does not exist. Let's create it."
      HEADER="scw dt0 t_start_ijd t_start t_end duration t_peak t_peak_ijd mu std snr_G snr_P snr_peak_G snr_peak_P net_cts pif_coverage good"
       echo "${HEADER}" > "${FLARES_REV_FILE}"
  else
      echo "${FLARES_REV_FILE} does exists. Let's append to it."
  fi
  for f in `ls ${HOME}/${SOURCE}/flares/${rev}????0010_flares_${SIGMA}s.csv`; do
      tail -n +2 $f >> ${FLARES_REV_FILE}
  done # f
done # rev


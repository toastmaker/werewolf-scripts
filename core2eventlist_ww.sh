#!/bin/bash

# werewolf

SOURCE="$1"
SCW="$2"
CATALOG="$3"

E_MIN="18"
E_MAX="250"

# DATALEVEL="000"
DATALEVEL="001"

echo "Let's create mask and eventlist for ${SOURCE} in ${SCW} with position from ${CATALOG}"
echo "Energy range for eventlist from ${E_MIN} to ${E_MAX} keV"

# Sanity check
[ "x$1" = "x" ] && echo -e "you forgot to define SOURCE.\nUsage core2events_ww.sh SOURCE SCW CATALOG" && exit 1
[ "x$2" = "x" ] && echo -e "you forgot to define SCW.\nUsage core2events_ww.sh SOURCE SCW CATALOG" && exit 1
[ "x$3" = "x" ] && echo -e "you forgot to define CATALOG.\nUsage core2events_ww.sh SOURCE SCW CATALOG" && exit 1

REV=${SCW:0:4}

if [ "${HOSTNAME}" = werewolf.lambrate.inaf.it ]; then 
	echo "running on werewolf..."
	LOCAL_DIR=${HOME}
else
	SSD_DIR=`get_ssd`
	echo "get_ssd returned ${SSD_DIR}"
        #
	LOCAL_DIR="${SSD_DIR}/toast_by_${USER}"
fi

SCRIPTS_DIR="/home/topinka/scripts" # former $HOME/SGR/scripts
WORKING_DIR="${LOCAL_DIR}/osa_workspace/${SOURCE}/${SCW}"
OUTPUT_DIR="/storage/${USER}/${SOURCE}"
echo "Working directory is ${WORKING_DIR}"

#### [ -d "${WORKING_DIR}" ] && rm -rf ${WORKING_DIR} # exit 0

mkdir -p "${WORKING_DIR}"
cd "${WORKING_DIR}"

if [ "${REV}" -lt 1626 ]; then
  echo "Rev ${REV}: Using OSA 10.2"
  ln -s /share/apps/mario/INTEGRAL/ic_tree/10.2/cat
  ln -s /share/apps/mario/INTEGRAL/ic_tree/10.2/ic
  ln -s /share/apps/mario/INTEGRAL/ic_tree/10.2/idx
  ln -s /anita/archivio/scw scw
  ln -s /anita/archivio/aux aux
  export ISDC_ENV=/share/apps/mario/INTEGRAL/osa10.2
else
  echo "Rev ${REV}: Using OSA 11.2"
  ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/cat
  ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/ic
  ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/idx
  ln -s /anita/archivio/scw scw
  ln -s /anita/archivio/aux aux
  export ISDC_ENV=/share/apps/mario/INTEGRAL/osa11.2
fi

export REP_BASE_PROD="${PWD}"

export ISDC_REF_CAT=${WORKING_DIR}/cat/hec/gnrl_refr_cat_0043.fits[1]
# export ISDC_REF_CAT=${WORKING_DIR}/cat/hec/gnrl_refr_cat_0041.fits[1]

. ${ISDC_ENV}/bin/isdc_init_env.sh

echo "scw/${SCW:0:4}/${SCW}.${DATALEVEL}/swg.fits[1]" > isgri.lst

export COMMONLOGFILE="+${SCW}_log.txt"
export COMMONSCRIPT=1

og_create idxSwg=isgri.lst ogid=iipif baseDir="./" instrument=IBIS 

cd obs/iipif

IC_DIR="${REP_BASE_PROD}/ic"
# CATALOG="${HOME}/${SOURCE}/catalog/SGR1806_ii_specat.fits"
ibis_science_analysis ogDOL="./og_ibis.fits" startLevel=COR endLevel=DEAD SCW1_GTI_gtiUserI=""

ii_pif inOG="" outOG="og_ibis.fits" inCat="${CATALOG}" \
		num_band=1 E_band_min=${E_MIN} E_band_max=${E_MAX} \
		mask="${IC_DIR}/ibis/mod/isgr_mask_mod_0003.fits" \
	tungAtt="${IC_DIR}/ibis/mod/isgr_attn_mod_0010.fits" \
	aluAtt="${IC_DIR}/ibis/mod/isgr_attn_mod_0011.fits" \
	leadAtt="${IC_DIR}/ibis/mod/isgr_attn_mod_0012.fits"

# barycenter=1

evts_extract group="og_ibis.fits" \
events="${SCW}_evts.fits" instrument=IBIS \
sources="${CATALOG}" gtiname="MERGED_ISGRI" \
pif=yes deadc=yes attach=no barycenter=0 timeformat=0 instmod=""


# setup python and heainit, hard-coded
echo "Initialising python, heasoft functions..."
source /share/apps/mario/setup/hesw.werewolf.bashrc
py3init
heainit 6.20

# update header
echo "Extending header info..."
"${SCRIPTS_DIR}/update_header.py" "${SCW}_evts.fits" "../../scw/${SCW:0:4}/${SCW}.${DATALEVEL}/isgri_events.fits.gz" "${SCW}_evts_h.fits"

# removing spare columns
echo "Removing columns TIMEDEL, BARYTIME_1, DEADC..."
echo "This is commented out"
# for col in TIMEDEL BARYTIME_1 DEADC; do
#   fdelcol "${SCW}_evts_h.fits+2" "${col}" N Y
# done

# copy results home
echo "Copying the output pif events..."
mkdir -p "${OUTPUT_DIR}/out/${SCW:0:4}"
cp "${SCW}_evts_h.fits" "${OUTPUT_DIR}/out/${SCW:0:4}"

echo "Gzipping..."
gzip -9 "${OUTPUT_DIR}/out/${SCW:0:4}/${SCW}_evts_h.fits"

echo "Copying the output mask..."
mkdir -p "${OUTPUT_DIR}/masks/${SCW:0:4}"
cp "scw/${SCW}.${DATALEVEL}/isgri_model.fits" "${OUTPUT_DIR}/masks/${SCW:0:4}/${SCW}_isgri_model.fits"
echo "Gzipping..."
gzip -9 "${OUTPUT_DIR}/masks/${SCW:0:4}/${SCW}_isgri_model.fits"

echo "Cleaning... Deleting working directory ${WORKING_DIR}"
rm -rf ${WORKING_DIR}

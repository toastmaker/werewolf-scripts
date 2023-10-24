#!/bin/bash

# source info
flare_start=$1
flare_end=$2
SCW=054700530010
REV=${SCW:0:4}
CATALOG="${HOME}/catalogs/SGR1806_ii_specat.fits"
echo "scw: $SCW, rev: $REV"

echo "initialising OSA...."
echo "Rev ${REV}: Using OSA 11.2"

ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/cat
ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/ic
ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/idx
ln -s /anita/archivio/scw scw
ln -s /anita/archivio/aux aux
export ISDC_ENV=/share/apps/mario/INTEGRAL/osa11.2

export REP_BASE_PROD="${PWD}"
export ISDC_REF_CAT="${REP_BASE_PROD}/cat/hec/gnrl_refr_cat_0043.fits[1]"
. ${ISDC_ENV}/bin/isdc_init_env.sh

echo "scw/${SCW:0:4}/${SCW}.001/swg.fits[1]" > isgri.lst
export COMMONLOGFILE="+${SCW}_log.txt"

#unset COMMONSCRIPT
export COMMONSCRIPT=1
og_create idxSwg=isgri.lst ogid=spe baseDir="./" instrument=IBIS
cd obs/spe

gti_user gti=flare_gti.fits begin=${flare_start} end=${flare_end} group=og_ibis.fits\[1] unit='day' clobber='yes'
chmod -w flare_gti.fits

export HEADAS="/share/apps/mario/HEASOFT/heasoft-6.20/x86_64-unknown-linux-gnu-libc2.18"
. ${HEADAS}/headas-init.sh

#ibis_science_analysis
# $ISDC_REF_CAT[ISGRI_FLAG>0]
# [ISGR_FLUX_1>300]]
#export ISDC_REF_CAT="$HOME/catalogs/gnrl_refr_cat_0043_1line.fits[1]"
ibis_science_analysis ogDOL="./og_ibis.fits" startLevel=COR endLevel=SPE CAT_refCat="$ISDC_REF_CAT[ISGRI_FLAG>0]" SCW1_GTI_gtiUserI="${USER_GTI}" SCW2_cat_for_extract="${CATALOG}" IBIS_nregions_spe=1 IBIS_nbins_spe="16" IBIS_energy_boundaries_spe="20 500" # IBIS_NoisyDetMethod=0


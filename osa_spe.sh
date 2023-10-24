#!/bin/bash
#
# script to create a spectrum from start_ijd to end_ijd 
# default catalog SGR1806

usage() { echo "Usage: $0 [-h] [-n <nbins> -e <energy_boundaries> ]  [-c <catalog.fits>] [--imgmin <low_energy_boundaries> ] [ --imgmax <high_energy_boundaries> ]  identifier scw start_ijd end_ijd" 1>&2; exit 1; }

#
# example: 
#
# ./osa_spe.sh -c "/home/topinka/catalogs/SGR1935s_ii_specat.fits" -n "-10 -1 1" -e "20 100 200 500" test 222200240010 7423.608025335649   7423.608026956019

CATALOG="${HOME}/catalogs/SGR1806_ii_specat.fits"
nregions_spe="2"
nbins_spe="-10 1"
energy_boundaries_spe="20 100 200"

ChanNum=3
E_band_min="20 40 100"
E_band_max="40 100 150"

while getopts ":c:n:e:h-:" o; do
    case "${o}" in
         -)
            case "${OPTARG}" in
                imgmin)
                    E_band_min="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    echo "Parsing option: '--${OPTARG}', value: '${E_band_min}'";
                    ;;
                imgmax)
                    E_band_max="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    echo "Parsing option: '--${OPTARG}', value: '${E_band_max}'";
                    ;;
##                imgmin=*)
#                    E_band_min=${OPTARG#*=}
#                    opt=${OPTARG%=${E_band_min}}
#                    echo "Parsing option: '--${opt}', value: '${E_band_min}'"
#                    ;;
            esac
            ;;
        c)
            CATALOG=${OPTARG}
            echo "Overwriting catalog with $CATALOG"
            ;;
        n)
            nbins_spe=${OPTARG}
            ;;
        e)
            energy_boundaries_spe=${OPTARG}
            ;;
        h)  
            usage
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

nregions_spe=`echo "${nbins_spe}" | wc -w`

ChanNum=`echo "${E_band_min}" | wc -w`

#if [ -z "${s}" ] || [ -z "${p}" ]; then
#    usage

if [ -z "$1" ]; then
  usage
fi

name=$1
SCW=$2
REV=${SCW:0:4}
# in IJD
flare_start=$3 # 2654.6141399311414
flare_end=$4 # 2654.6141453709565

echo "name: $name"
echo "scw: $SCW, rev: $REV"
echo "start_ijd: ${flare_start}"
echo "end_ijd: ${flare_end}"
echo "catalog: $CATALOG"

echo "nregions_spe = $nregions_spe"
echo "nbins_spe = $nbins_spe"
echo "energy_boundaries_spe = $energy_boundaries_spe"

echo "image ChanNum = $ChanNum"
echo "image  E_band_min = ${E_band_min}"
echo "image  E_band_max = ${E_band_max}"

# echo "Exiting..."
# exit 0

mkdir -p "spe_${name}"
cd "spe_${name}"

echo "initialising OSA...."
echo "Using OSA 11.2"
ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/cat
ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/ic
ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/idx
ln -s /anita/archivio/scw scw
ln -s /anita/archivio/aux aux
export ISDC_ENV=/share/apps/mario/INTEGRAL/osa11.2
export REP_BASE_PROD="${PWD}"
export ISDC_REF_CAT="${REP_BASE_PROD}/cat/hec/gnrl_refr_cat_0043.fits[1]"
. ${ISDC_ENV}/bin/isdc_init_env.sh

echo "initialising HEASOFT"
export HEADAS="/share/apps/mario/HEASOFT/heasoft-6.20/x86_64-unknown-linux-gnu-libc2.18"
. ${HEADAS}/headas-init.sh

echo "Creating group..."
echo "scw/${SCW:0:4}/${SCW}.001/swg.fits[1]" > isgri.lst
export COMMONLOGFILE="+${SCW}_log.txt"
export COMMONSCRIPT=1
og_create idxSwg=isgri.lst ogid=spe baseDir="./" instrument=IBIS

echo "Creating a user GTI..."
cd obs/spe
USER_GTI=flare_gti.fits
gti_user gti="${USER_GTI}" begin=${flare_start} end=${flare_end} group=og_ibis.fits\[1] unit='day' clobber='yes'
chmod -w flare_gti.fits

echo "Running OSA..."

# unset COMMONSCRIPT
# ibis_science_analysis
# exit 0


ibis_science_analysis ogDOL="./og_ibis.fits" \
    startLevel=COR endLevel=SPE \
    CAT_refCat="$ISDC_REF_CAT[ISGRI_FLAG>0]" \
    SCW1_GTI_gtiUserI="${USER_GTI}" \
    SCW2_cat_for_extract="${CATALOG}" \
    IBIS_II_ChanNum="${ChanNum}" \
    IBIS_II_E_band_min="${E_band_min}" \
    IBIS_II_E_band_max="${E_band_max}" \
    IBIS_nregions_spe="${nregions_spe}" IBIS_nbins_spe="${nbins_spe}" IBIS_energy_boundaries_spe="${energy_boundaries_spe}" \
    IBIS_NoisyDetMethod=0

echo "Copying results..."
outdir="${REP_BASE_PROD}/result"
mkdir -p ${outdir}
cp scw/${SCW}.001/isgri_spectrum.fits "${outdir}/${name}_isgri_spectrum.fits"
rmf=`ls isgr_rmf_ebds_????_rbn.fits`
echo "rmf = $rmf"
cp ${rmf} "${outdir}"
fthedit "${outdir}/${name}_isgri_spectrum.fits" keyword=RESPFILE operation=add value="${rmf}"
fthedit "${outdir}/${name}_isgri_spectrum.fits[1]" keyword=RESPFILE operation=add value="${rmf}"
fthedit "${outdir}/${name}_isgri_spectrum.fits[2]" keyword=RESPFILE operation=add value="${rmf}"
fthedit "${outdir}/${name}_isgri_spectrum.fits[3]" keyword=RESPFILE operation=add value="${rmf}"

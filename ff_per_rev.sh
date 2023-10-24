# define revolutions

CONFIG=$1
[ "x${CONFIG}" = "x" ] && echo -e "Define config.json argument!\nUsage: ff_per_rev.sh config.json" && exit 1

SCRIPTS_DIR=${HOME}/scripts # default main script dir, former ~/SGR/scripts

# config crucial variables
SOURCE=`jq -r '.SOURCE' < ${CONFIG}`
REV_LIST=$( jq -r '.REV_LIST' < ${CONFIG} )
FF_PAR=$( jq -r '.FF_PAR' < ${CONFIG} ) 

E_MIN=$( jq -r '.low_e' < ${FF_PAR} )
E_MAX=$( jq -r '.high_e' < ${FF_PAR} )

echo "E_min = ${E_MIN}, E_max = ${E_MAX}"

if [ "${FF_PAR}" = "null" ]; then FF_PAR_OPT=""; else FF_PAR_OPT="--par ${FF_PAR}"; fi

BATCH_SIZE=128 #128 # 64 #64
SIGMA=6 # use INTEGER, otherwise ${SIGMA}.0 later would cause an error

if [ -z ${E_MIN} ]; then
  echo "E_MIN not defined"
  FLARES_DIR="${HOME}/${SOURCE}/flares"
  FFLOGS_DIR="${HOME}/${SOURCE}/fflogs"
else
  FLARES_DIR="${HOME}/${SOURCE}/flares_${E_MIN}_${E_MAX}"
  FFLOGS_DIR="${HOME}/${SOURCE}/fflogs_${E_MIN}_${E_MAX}"
fi

mkdir -p "${FLARES_DIR}"
mkdir -p "${FFLOGS_DIR}"

REV_DONE_LIST="${REV_LIST}.done"
# "${HOME}/SGR/lists/sgr1806_fov.rev.done"
# "${HOME}/SGR/lists/sgr1806_fov.rev"

SEARCH_DONE_LIST="${REV_LIST}.searched"

# revs=$( for rev in `cat "${REV_DONE_LIST}"`; do [ -f "${FLARES_DIR}/${rev:0:4}_flares_${SIGMA}s.csv" ] || echo "${rev:0:4}";  done | head -n ${BATCH_SIZE} )
revs=$( for rev in `cat "${REV_DONE_LIST}"`; do  ( grep -q "$rev" "${SEARCH_DONE_LIST}" ) || echo "${rev:0:4}";  done | head -n ${BATCH_SIZE} )

# revs="1208 1209 1210"

COUNT=$( wc -w <<< "${revs}" )
echo "considering ${COUNT} revs: ${revs}"


for rev in ${revs}; do

  [[ ! -d "/storage/topinka/${SOURCE}/out/${rev}" ]] && echo "/storage/topinka/${SOURCE}/out/${rev} does not exist" && continue # no data

  # create a script to run the flare search
  QSCRIPT="${HOME}/${SOURCE}/qscripts/ff0_${rev}_p.sh"
  echo "#!/bin/bash" > "${QSCRIPT}"
  echo "${SCRIPTS_DIR}/ffinder2.py -v --isgri-eventlist=\"/anita/archivio/scw/{rev}/{scw}.001/isgri_events.fits.gz\" -o \"${FLARES_DIR}/${rev}_flares_${SIGMA}s.csv\" -d \"/storage/topinka/${SOURCE}/out/${rev}\" -s ${SIGMA}.0 -w ${FF_PAR_OPT}" >> "${QSCRIPT}"
  echo "echo ${rev} >> ${SEARCH_DONE_LIST}"  >> "${QSCRIPT}"
  chmod +x "${QSCRIPT}"
  echo "Submitting ${QSCRIPT} ..."

  qsub -q iasf -o ${FFLOGS_DIR}/${rev}.out -j oe -N "ff_${SOURCE}_${rev}" "${QSCRIPT}"
done

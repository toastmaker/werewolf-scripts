#!/bin/bash
CONFIG=$1
[ "x${CONFIG}" = "x" ] && echo -e "Define config.json argument!\nUsage: ff_per_rev.sh config.json" && exit 1

source /share/apps/mario/setup/hesw.werewolf.bashrc
heainit
idlinit

SCRIPTS_DIR=${HOME}/scripts # default main script dir, former ~/SGR/scripts

# config crucial variables
SOURCE=`jq -r '.SOURCE' < ${CONFIG}`
SCW_LIST=`jq -r '.SCW_LIST' < ${CONFIG}`
REV_LIST=$( jq -r '.REV_LIST' < ${CONFIG} )
SRC_RA=$( jq -r '.SRC_RA' < ${CONFIG} )
SRC_DEC=$( jq -r '.SRC_DEC' < ${CONFIG} )

BATCH_SIZE=256 #1 #64
SIGMA=6 # use INTEGER, otherwise ${SIGMA}.0 later would cause an error

REV_DONE_LIST="${REV_LIST}.done"
# "${HOME}/SGR/lists/sgr1806_fov.rev.done"
# "${HOME}/SGR/lists/sgr1806_fov.rev"

revs=$( for rev in `cat "${REV_DONE_LIST}"`; do [ -f "${HOME}/${SOURCE}/flares/${rev:0:4}_flares_${SIGMA}s.csv" ] || echo "${rev:0:4}";  done | head -n ${BATCH_SIZE} )

# revs="1208 1209 1210"

COUNT=$( wc -w <<< "${revs}" )
echo "considering ${COUNT} revs: ${revs}"

# exit 0

IDL=/lnx/swsrv/idl/idl88/bin/idl

for rev in ${revs}; do

  scws=$( grep -e "^${rev}" ${SCW_LIST} )
  SCW_COUNT=$( wc -w <<< "${scws}" )
  echo "considering ${SCW_COUNT} scws from rev ${rev}"
  for scw in ${scws}; do
    [ -f temp_checkscw.txt ] && rm temp_checkscw.txt
    ${IDL} -e "checkscw, 0, '/anita/archivio/scw/', '${scw}', 246.998, -52.5845" 2> /dev/null 1> /dev/null
    redchi=$(awk '{print $30}' temp_checkscw.txt)
    if (( $( echo "${redchi} < 5.0" | bc -l) )); then


      echo "$scw $redchi good"

      [[ ! -d "/storage/topinka/${SOURCE}/out/${rev}" ]] && echo "/storage/topinka/${SOURCE}/out/${rev} does not exist" && continue # no data

      # create a script to run the flare search
      QSCRIPT="${HOME}/${SOURCE}/qscripts/ff0_${scw}_p.sh"
      echo "#!/bin/bash" > "${QSCRIPT}"
      echo "${SCRIPTS_DIR}/ffinder2.py -v -o \"${HOME}/${SOURCE}/flares/${scw}_flares_${SIGMA}s.csv\" -s ${SIGMA}.0 -w /storage/topinka/${SOURCE}/out/${rev}/${scw}_evts_h.fits.gz" >> "${QSCRIPT}"
      chmod +x "${QSCRIPT}"
      echo "Submitting ${QSCRIPT} ..."

      qsub -q iasf -o ${HOME}/${SOURCE}/fflogs/${scw}.out -j oe -N "ff_${SOURCE}_${scw}" "${QSCRIPT}"
    else
      echo "$scw $redchi bad"
    fi
  done
done


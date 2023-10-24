#!/bin/bash

# define revolutions

# revs=$( grep -E '(0056)|(0057)' ${HOME}/SGR/lists/sgr1806_fov.rev )

# revs=$( seq 100 121 )

#revs="0046 0050 0051 0052 0053 0054 0055 0058 0059 0060 0061 0062 0063 0064 0065 0066 0067"

# revs="0123 0164 0165 0167 0168 0169 0171 0172 0173 0174 0175 0178 0179"

BATCH_SIZE=10 # 1
# qsub resources allocation
LOPT="-l nodes=1:ppn=4"

CONFIG=$1
[ "x${CONFIG}" = "x" ] && echo -e "Define config.json argument!\nUsage: run_per_rev.sh config.json" && exit 1

SCRIPTS_DIR=/home/topinka/scripts # default main script dir, former ~/SGR/scripts

# config crucial variables
SOURCE=`${SCRIPTS_DIR}/jq -r '.SOURCE' < ${CONFIG}`
SCW_LIST=$( ${SCRIPTS_DIR}/jq -r '.SCW_LIST' < ${CONFIG} )
REV_LIST=$( ${SCRIPTS_DIR}/jq -r '.REV_LIST' < ${CONFIG} )
CATALOG=$( ${SCRIPTS_DIR}/jq -r '.CATALOG' < ${CONFIG} )

echo "Configuration"
echo "SOURCE: ${SOURCE}"
echo "SCW_LIST: ${SCW_LIST}"
echo "REV_LIST: ${REV_LIST}"
echo "CATALOG: ${CATALOG}"

[[ ! -f ${SCW_LIST} ]] && echo "Can't find SCW_LIST file ${SCW_LIST}" &&  exit 0
[[ ! -f ${REV_LIST} ]] && echo "Can't find REV_LIST file ${REV_LIST}" &&  exit 0 
[[ ! -f ${CATALOG} ]] && echo "Can't find CATALOG file ${CATALOG}" &&  exit 0

#SOURCE="SGR"
#SCW_LIST="${HOME}/${SOURCE}/lists/sgr1806_fov.scw"
#REV_LIST="${HOME}/${SOURCE}/lists/sgr1806_fov.rev"
#CATALOG="${HOME}/${SOURCE}/catalog/sgr1806_ii_specat.fits"

mkdir -p ${HOME}/${SOURCE}/lists
mkdir -p ${HOME}/${SOURCE}/qscripts
mkdir -p ${HOME}/${SOURCE}/logs

# list of currently running jobs
qstat | grep ${USER} | awk '{print $2}' > ${HOME}/${SOURCE}/lists/pending.rev

# revs=$( for rev in `cat "${REV_LIST}"`; do [ grep ${rev} "${REV_LIST}.done" ] || echo "${rev:0:4}";  done | head -n ${BATCH_SIZE} )

# create an empty revlist.done if it does not exist
[  -f ${REV_LIST}.done ] || touch ${REV_LIST}.done

# skip if rev in done, or rev in currently running
revs=$( for rev in `cat "${REV_LIST}"`; do QNAME="${SOURCE}_${rev}"; QNAME=${QNAME:0:10}; ( grep -q "${rev}" "${REV_LIST}.done" || grep -q "${QNAME}" ${HOME}/${SOURCE}/lists/pending.rev ) || echo "${rev:0:4}";  done | head -n ${BATCH_SIZE} )

COUNT=$( wc -w <<< "${revs}"  )
echo "considering ${COUNT} revs: ${revs}"

# exit 0

for rev in ${revs}; do
# create scw lists for each rev
#  [ -f "${HOME}/${SOURCE}/lists/${rev}_fov.scw" ] && rm "${HOME}/${SOURCE}/lists/${rev}_fov.scw"
#  for scw in `cat "${HOME}/${SOURCE}/lists/sgr1806_fov.scw" | grep "^${rev}"`; do
#    echo ${scw} >> "${HOME}/${SOURCE}/lists/${rev}_fov.scw" 
#  done

  grep "^${rev}" ${SCW_LIST} > "${HOME}/${SOURCE}/lists/${rev}_fov.scw"

  QSCRIPT="${HOME}/${SOURCE}/qscripts/run0_${rev}_p.sh"
  echo "#!/bin/bash" > "${QSCRIPT}"
  echo "# script to run rev ${rev}" >> "${QSCRIPT}"
  echo "for scw in \`cat ${HOME}/${SOURCE}/lists/${rev}_fov.scw\`; do" >> "${QSCRIPT}" 
  echo "${SCRIPTS_DIR}/core2eventlist_ww.sh ${SOURCE} \${scw} ${CATALOG}" >> "${QSCRIPT}"
  echo "done" >> "${QSCRIPT}"
  echo "echo \"${rev}\" >> \"${REV_LIST}.done\"" >>  "${QSCRIPT}" # flag that the work is done
  chmod +x "${QSCRIPT}"
  echo "Submitting ${QSCRIPT} ..."
  
  qsub -q iasf ${LOPT} -o ${HOME}/${SOURCE}/logs/${rev}.out -j oe -N "${SOURCE}_${rev}" "${QSCRIPT}"
#  echo "Would submit: qsub -q iasf -o ${HOME}/${SOURCE}/logs/${rev}.out -j oe -N ${SOURCE}_${rev} ${QSCRIPT}"
  
done

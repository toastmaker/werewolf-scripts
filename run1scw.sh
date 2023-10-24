CONFIG=$1
scw=$2

[ "x${CONFIG}" = "x" ] && echo -e "Define config.json argument!\nUsage: run1scw.sh config.json SCW" && exit 1

[ "x${scw}" = "x" ] && echo -e "Define scw to analyse!\nUsage: run1scw.sh config.json SCW" && exit 1

SCRIPTS_DIR=${HOME}/scripts # default main script dir, former ~/SGR/scripts

# config crucial variables
SOURCE=`${SCRIPTS_DIR}/jq -r '.SOURCE' < ${CONFIG}`
CATALOG=$( ${SCRIPTS_DIR}/jq -r '.CATALOG' < ${CONFIG} )

echo "Configuration"
echo "SOURCE: ${SOURCE}"
echo "CATALOG: ${CATALOG}"
echo "SCW: ${scw}"

[[ -f ${CATALOG} ]] || ( echo "Can't find CATALOG file ${CATALOG}" &&  exit 0 )

QSCRIPT="${HOME}/${SOURCE}/qscripts/run1_${scw}.sh"

echo "${SCRIPTS_DIR}/core2eventlist_ww.sh ${SOURCE} ${scw} ${CATALOG}" > "${QSCRIPT}"
chmod +x "${QSCRIPT}"
qsub -q iasf -o ${HOME}/${SOURCE}/logs/${scw}.out -j oe -N "${SOURCE}_${scw}" "${QSCRIPT}"

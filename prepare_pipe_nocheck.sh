#!/bin/bash

# Example:
# SRC=4U0142
# RA=26.5933
# DEC=61.7509

SCRIPTDIR="/home/topinka/scripts"
CATDIR="/home/topinka/catalogs"

SRC=$1
RA=$2
DEC=$3

[ "x${SRC}" = "x" ] && echo "Missing args..." &&  exit 1
[ "x${RA}" = "x" ]  && echo "Missing args..." &&  exit 1 
[ "x${DEC}" = "x" ] && echo "Missing args..." &&  exit 1

echo "Get pipeline ready for source ${SRC} at RA=${RA}, DEC=${DEC}"

echo "Make catalog..."
echo "Searching for catalog in ${CATDIR}"
[ -f ${HOME}/catalogs/${SRC}_ii_specat.fits ] || ${HOME}/scripts/makesrccat.py ${SRC} ${RA} ${DEC}  "${HOME}/catalogs/${SRC}_ii_specat.fits"

echo "Build dirs..."
mkdir -p ${HOME}/${SRC}
cd ${HOME}/${SRC}
mkdir -p lists logs config


echo "Find scws in ISDC..."
echo "Skipped"
#cd ${HOME}/${SRC}/lists
# CMD="${HOME}/scripts/scwfinder.py"
# for year in `seq 2003 2021`; do ${CMD} ${RA} ${DEC} "${year}-01-01 00:00:00" "${year}-06-30 23:59:59" | grep '10$'; ${CMD} ${RA} ${DEC} "${year}-07-01 00:00:00" "${year}-12-31 23:59:59" | grep '10$'; done > ${SRC}.scw

# wc -l ${SRC}.scw

echo "Check scws..."
echo "Skipped"
# ${HOME}/scripts/idl_checkscw.sh ${SRC} ${RA} ${DEC} &> ${HOME}/${SRC}/lists/idl_checkscw_${SRC}.out

# echo "Select scws and in fov..."
# cat ${SRC}_scw_checked.txt | grep -v ^# | grep -v '\-999.000' | awk '(NR>0) { if ( ( $8*$8< 15*15) && ($9*$9 <15*15) ) { print substr($1,1,12) "0010" }}' | uniq > ${SRC}_fov.scw
# awk '{print substr($1,1,4)}' ${SRC}_fov.scw | uniq > ${SRC}_fov.rev
# wc -l ${SRC}_fov.scw
# wc -l ${SRC}_fov.rev

echo "Build config..."
cat > ${HOME}/${SRC}/config/${SRC}.json << EOL
{
  "SOURCE": "${SRC}",
  "SCW_LIST": "/home/topinka/${SRC}/lists/${SRC}_fov.scw",
  "REV_LIST": "/home/topinka/${SRC}/lists/${SRC}_fov.rev",
  "CATALOG":  "/home/topinka/catalogs/${SRC}_ii_specat.fits"
}
EOL

echo "${HOME}/${SRC}/config/${SRC}.json:"
cat ${HOME}/${SRC}/config/${SRC}.json

echo "All done."
echo "Add this line to crontab:"
echo "*/15 * * * * /home/topinka/scripts/queue_check_run_per_rev.sh /home/topinka/${SRC}/config/${SRC}.json &>> /home/topinka/${SRC}/logs/queue_check.cron"



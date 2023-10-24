#!/bin/bash
export PATH="${PATH}:/opt/pbs/bin"
config=$1
if [ ! -f "${config}" ]; then
  echo "Config file not found. Exiting..."
  exit 0
  fi

date
echo "Checking the queue (user ${USER})..."
qstat | grep ${USER}
if [ "x$( qstat | grep ${USER} )" = "x" ]; then
  echo "Queue is empty"
  echo "Ready to submit another batch of jobs with run_per_rev.sh..."
  echo "Config file ${config}"
  /home/topinka/scripts/run_per_rev.sh ${config}
  echo "run_per_rev.sh finished."
else
  echo "There are $(qstat | grep ${USER} | wc -l ) jobs running"
fi


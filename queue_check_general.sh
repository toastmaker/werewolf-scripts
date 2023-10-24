#!/bin/bash
export PATH="${PATH}:/opt/pbs/bin"

[ -z "$1" ] && echo "Usage: $0 'command'" && exit 1

date
echo "Checking the queue (user ${USER})..."
qstat | grep ${USER}
if [ "x$( qstat | grep ${USER} )" = "x" ]; then
  echo "Queue is empty"
  echo "Ready to submit another batch of jobs..."
  echo "Executing: $1"
  $1
  echo "Finished."
else
  echo "There are $(qstat | grep ${USER} | wc -l ) jobs running"
fi


#!/bin/bash
echoerr() { echo "$@" 1>&2; }
th=1.1
while getopts ":t:" o; do
    case "${o}" in
        t)
            th=${OPTARG}
#            echoerr "Threshold set to $th"
            ;;
    esac
done
shift $((OPTIND-1))

dbfile="/home/topinka/db/big_scwcheck.db"

# echo "first = $1"
if [ -z $1 ]; then
  while read scw; do sqlite3 ${dbfile} "select ScW from scws where ScW=='${scw}' and chired < $th;"; done
else
  while read scw; do sqlite3 ${dbfile} "select ScW from scws where ScW=='${scw}' and chired < $th;"; done < $1
fi

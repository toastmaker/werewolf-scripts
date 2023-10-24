#!/bin/bash
echoerr() { echo "$@" 1>&2; }
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

if [ -z $1 ]; then
  while read scw; do found=$( sqlite3 ${dbfile} "select ScW from scws where ScW=='${scw}'" ); if [ -z $found ]; then echo $scw; fi done
else
  while read scw; do found=$( sqlite3 ${dbfile} "select ScW from scws where ScW=='${scw}'" ); if [ -z $found ]; then echo $scw; fi done
fi

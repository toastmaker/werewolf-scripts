#/bin/bash

fullfile=$1
filename=$(basename -- "$fullfile")
extension="${filename##*.}"
filename="${filename%.*}"


cat ${fullfile} | grep -v ^# | grep -v '\-999.000' | awk '(NR>0) { if ( ( $7*$7< 15*15) && ($6*$6 <15*15) ) { print substr($2,1,12)}}' > "${HOME}/SGR/lists/${filename}_fov.scw"

awk '{print substr($1,1,4)}' "${HOME}/SGR/lists/{filename}_fov.scw" | uniq > "${filename}_fov.rev"

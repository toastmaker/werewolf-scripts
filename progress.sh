#!/bin/bash
source=$1
total=$( wc -l ${HOME}/${source}/lists/${source}_fov.rev | awk '{ print $1 }' )
finished=$( wc -l ${HOME}/${source}/lists/${source}_fov.rev.done | awk '{ print $1 }' )
perc=$( echo "scale=2; 100*${finished} / ${total}" | bc -l )

printf "%s %d of %d (%.1f%%) revs done\n" "${source}" ${finished} ${total} "${perc}"


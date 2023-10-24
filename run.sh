#rev="0122"
rev=$1

[ -f "${HOME}/SGR/lists/${rev}_fov.scw" ] || (echo "${HOME}/SGR/lists/${rev}_fov.scw does not exist" && exit 0)

n=$( cat "${HOME}/SGR/lists/${rev}_fov.scw" | wc -l )
echo "Submitting $n single jobs for rev ${rev}"

for scw in `cat ${HOME}/SGR/lists/${rev}_fov.scw`; do

echo "${HOME}/SGR/scripts/core2eventlist_ww.sh ${scw}" > "${HOME}/SGR/scripts/run0.sh"
chmod +x "${HOME}/SGR/scripts/run0.sh"
qsub -q iasf -o ${HOME}/SGR/logs/${scw}.out -j oe -N "${scw}" "${HOME}/SGR/scripts/run0.sh"
done

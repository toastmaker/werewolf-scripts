SCW_LIST=$1
RUNSCRIPT=/home/topinka/scripts/scwheader2sqlite.py
DB_FILE=/home/topinka/db/scwcheck.db

for scw in `cat "${SCW_LIST}"`; do
  rev=${scw:0:4}
  ${RUNSCRIPT} /anita/archivio/scw/${rev}/${scw}.001/isgri_events.fits.gz ${DB_FILE}
done

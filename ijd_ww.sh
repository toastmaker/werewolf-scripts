#!/bin/bash

# werewolf

IJD="$1"
LOCAL_DIR=${HOME}
WORKING_DIR="${LOCAL_DIR}/IJD"
mkdir -p "${WORKING_DIR}"
cd "${WORKING_DIR}"

ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/cat
ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/ic
ln -s /share/apps/mario/INTEGRAL/ic_tree/11.2/idx
ln -s /anita/archivio/scw scw
ln -s /anita/archivio/aux aux
export ISDC_ENV=/share/apps/mario/INTEGRAL/osa11.2
export REP_BASE_PROD="${PWD}"
export ISDC_REF_CAT="dummy"
export ISDC_OMC_CAT="dummy"
. ${ISDC_ENV}/bin/isdc_init_env.sh
OUTPUT=$( converttime IJD $IJD UTC )
echo "$OUTPUT" | gawk 'match($0, /^Log_1  : Input Time\(IJD\):\s+(.+)\s+Output Time\(UTC\):\s+(.+)$/, a) {print a[2]}'
rm -rf ${WORKING_DIR}

#!/bin/bash
SRC=$1
RA=$2
DEC=$3

source /share/apps/mario/setup/hesw.werewolf.bashrc
heainit
idlinit

/lnx/swsrv/idl/idl88/bin/idl -e "checkscw_scwloop,'/anita/archivio/scw/','/home/topinka/${SRC}/lists/${SRC}_scw_checked.txt','/home/topinka/${SRC}/lists/${SRC}.scw', ${RA}, ${DEC}"

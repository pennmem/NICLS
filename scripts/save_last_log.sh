#!/bin/bash

if [  $# -le 1 ]
then
    echo "Usage: save_last_log.sh [subject] [session]"
    exit 1
fi

SUB=$1
SESS=$2
EXP="NiclsCourierClosedLoop"

LASTLOG=`ls -t ../data/logs/ | head -n1`
echo "Last log was: ${LASTLOG}"
scp ../data/logs/${LASTLOG} maint@rhino2.psych.upenn.edu:/data/eeg/scalp/ltp/${EXP}/${SUB}/session_${SESS}/nicls.log

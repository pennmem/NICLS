#!/bin/bash

if [  $# -le 1 ]
then
    echo "Usage: save_last_log.sh [subject] [session]"
    exit 1
fi

SUB=$1
SESS=$2
EXP="NiclsCourierClosedLoop"

LASTLOG=`ls -t ../data/ | head -n1`
echo "Last log was: ${LASTLOG}"
if [[ "$LASTLOG" == *.jsonl ]]
then
    scp ../data/logs/${LASTLOG} maint@rhino2.psych.upenn.edu:/data/eeg/scalp/ltp/${EXP}/${SUB}/session_${SESS}/nicls.log
else
    echo "Not a valid log file. Check paths."
    exit 1
fi

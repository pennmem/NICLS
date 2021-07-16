#!/bin/bash

if [  $# -le 0 ]
then
    echo "Usage: pull_classifier.sh [subject_id]"
    exit 1
fi


SUBJECT=$1

mkdir -p ~/NICLS/data/classifiers/

scp "maint@rhino2.psych.upenn.edu:/data/eeg/scalp/ltp/NiclsCourierReadOnly/${SUBJECT}/nicls_${SUBJECT}_classifier.json" ~/NICLS/data/classifiers/

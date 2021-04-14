JPB: TODO: Convert to rst

# NICLS
This is the backend for the NICLS Experiment
This connects the Courier Task and biosemi to a backend that runs a classifier
The classifier determines when the participant in the Task should receive a new word

## Installation
1. pip install numpy aiofiles django
1. pip install -e ./nicls 

## Generate Installer
JPB: TODO: Add installer instructions here

## Run Tests
1. install the nicls module
	pip install -e ./nicls 
1. run the tests
	cd tests
	python3 main.py
1. check results (JPB: TODO: add more description here)
	Print to screen
	Create data folder and log the data there

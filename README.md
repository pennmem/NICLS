# NICLS
This is the backend for the NICLS Experiment
This connects the Courier Task and biosemi to a backend that runs a classifier
The classifier determines when the participant in the Task should receive a new word

## Installation
Create conda environment
1. conda create -n <NAME> python=3.9

Install ptsa_new first
1. conda install -y -c pennmem fftw
1. conda install -y numpy scipy xarray swig traits
1. git clone https://github.com/pennmem/ptsa_new.git
1. cd ptsa_new
1. python setup.py install
1. cd ..

Install NICLServer
1. python setup.py install

1. pip3 install numpy aiofiles django zmq scikit-learn
1. pip3 install -e ./NICLS

## Run Tests (under development)
1. install the nicls module
	pip install -e ./nicls 
1. run the tests
	cd tests
	python3 main.py
1. check results (JPB: TODO: add more description here)
	Print to screen
	Create data folder and log the data there

## More information
Please see the docs folder for more information

JPB: TODO: Convert to rst

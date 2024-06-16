# NICLS
This repository contains the backend (data collection, processing, and classification) for the Non-invasive Closed-Loop Stimulus-presentation (NICLS) experiment (see https://doi.org/10.1101/2023.08.25.553563).

This connects the behavioral task (a Unity application) and BioSemi EEG to a backend that classifies behaviorally relevant brain states and relays those results back to the task.

## Installation
Create and activate conda environment
1. `conda create -n NICLS python=3.9`
1. `conda activate NICLS`

Install ptsa_new first
1. `conda install -y -c pennmem fftw`
1. `conda install -y -c conda-forge cxx-compiler`
1. `conda install -y numpy scipy xarray swig traits`
1. `git clone https://github.com/pennmem/ptsa.git`
1. `cd ptsa`
1. `git checkout a4e9298`
1. `pip install -e .`
    1. OR: `python setup.py install`
1. `cd ..`

Install NICLServer
1. `pip install -e .`
    1. OR: `python setup.py install`
1. `cd ..`

## Run Tests (under development)

In order to run tests with fake biosemi data, you need to use `pennmem/eegim`,
which has been set up as a git submodule in this repository.

1. Initialize the submodules
    1. `git submodule update --init --recursive` 

1. Run the tests
    1. `cd tests`
    1. `python main1b.py (fake Courier & fake biosemi)`
    1. `python main2.py (fake Courier & real biosemi)`
    1. `python main3.py (real Courier & fake biosemi)`
    1. `cd ..`

1. Check results
    1. Classifier results will print to screen once enough biosemi data has collected
    1. Logs will be stored in the "data" folder

## More information
Please see the docs folder for more information

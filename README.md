# NICLS
This is the backend for the NICLS Experiment
This connects the Courier Task and biosemi to a backend that runs a classifier
The classifier determines when the participant in the Task should receive a new word

## Installation
Create and activate conda environment
1. conda create -n \<NAME\> python=3.9
1. conda activate \<NAME\>

Install ptsa_new first
1. conda install -y -c pennmem fftw
1. conda install -y -c conda-forge cxx-compiler
1. conda install -y numpy scipy xarray swig traits
1. git clone https://github.com/pennmem/ptsa_new.git
1. cd ptsa_new
1. python setup.py install
1. cd ..

Install NICLServer
1.git checkout dev/classifier 
1.python setup.py install

## Run Tests (under development)

In order to run tests with fake biosemi data, you need to use `pennmem/eegim`,
which has been set up as a git submodule in this repository.

Just run `git submodule init` followed by `git submodule update` to use the simulator for testing.

1. run the tests
    1. cd tests
    1. python main.py (without Courier)
    1. python main3.py (with Courier)

1. check results
    1. Classifier results will print to screen once enough biosemi data has collected
    1. Logs will be stored in the "data" folder

## More information
Please see the docs folder for more information

JPB: TODO: Convert to rst

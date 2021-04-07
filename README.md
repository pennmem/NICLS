# NICLS
This is the backend for the NICLS Experiment
This connects the Courier Task and biosemi to a backend that runs a classifier
The classifier determines when the participant in the Task should receive a new word

## Architecture
### Definitions
Data sources = Hardware that collects data about the participant such as the biosemi or an eyetracker
Task = The game that the participant plays (called Courier)

### Messaging System
Publish/Subscribe architecture using the django Signals library
It is a synchronous design (no queues or async waits). 
The handler functions will be called in the order that they subscribed.
The channels are based on the publisher ids provided by the Publisher class
Inherit the Publisher class to be able to publish and get a unique publisher ID
Inherit the Subscriber class to be able to subscribe

### Setup
When the system starts, this is the order of events
1. main file creates the TaskServer thread and DataLogger thread
1. task server then starts the classifier(s) and the data source(s) using the values in the config file
1. task server subscribes to all the classifiers
1. classifiers subscribe to the data sources that they care about
1. task server starts all the data sources

### Data Flow
When a data source publishes new data that arrived, this is the order of events
1. the classifiers that care will 
	1. receive the data
	1. copy and store it
	1. if enough data has been collected then it will spawn a NEW task to run the classifier
	1. the original task will return to the data source to resume awaiting more data
1. the new classifier task will
	1. create a new process to handle the computations and add it to the process pool
	1. await the result of the computations
	1. publish the result and finish
1. the task server will 
	1. receive the published results (remember that this is synchronous, so just a function call)
	1. create a NEW task to send the results to the task itself
	1. the original task will return to the classifier to finish
1. the new task server task will
	1. send the the results to the task itself and finish

### Design Diagram
<Name of file here>

## Test Arch
### Option 1
main creates the nicls server, a fake biosemi data source, and a fake task data source
### Option 2
main2 creates the nicls server and a fake task data source
A real biosemi source is used

## Generate Installer
???

## Setup
pip install numpy aiofiles django

## Tests
1) Install the nicls module
	pip install -e ./nicls 
2) Run the tests
	cd tests
	python3 main.py
3) Check Results (more description here)
	Print to screen
	Create data folder and log the data there

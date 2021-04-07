# NICLS
This is a project to ___

## Architecture
### File/Class Responsibility
main creates the TaskServer thread, EphysLogger thread (TODO), and DataLogger thread

### Messaging System
Publish/Subscribe architecture
The design is build around the publisher ids provided by the Publisher class
Inherit the Publisher class to be able to publish and get a unique publisher ID
Inherit the Subscriber class to be able to subscribe

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

# This is the project folder for the iottest project.

# Overview

## the agent

  - runs on the host with the mqtt container
  - starts sysdig and sends the recordings to the ids

## the ids

  - a python script with the actual ids algorithm
  - gets scap files via rest
  - does detection 
  - sends results to an other endpoint in json? format

## the test-container

  - a docker container
  - only used to test this locally -> this replaces the mqtt container


# Step by step guide

## Host
1. install sysdig into the host, see: https://github.com/draios/sysdig/wiki/How-to-Install-Sysdig-for-Linux
2. for testing
   - build the test container
   - start the test container
3. Agent
   - move to agent directory
   - install python dependencies: `sudo pip install -r requirements.txt`
   - start the agent script `sudo python3 agent.py target_container_name endpoint`
     - `sudo python3 agent.py happy_agnesi http://127.0.0.1:80/ids/upload_scap`

## IDS
   - install sysdig into the ids machine, see: https://github.com/draios/sysdig/wiki/How-to-Install-Sysdig-for-Linux
   - move to ids directory
   - install python dependencies: `sudo pip install -r requirements.txt`
   - run the ids_receiver script:`sudo python3 ids_receiver.py`
   - run the ids script: `python3 ids.py training`
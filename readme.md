# This is the project folder for the iottest project.

# Overview

## the agent

  - runs on the host with the mqtt container
  - starts sysdig and sends the recordings to the ids

## the ids

  - a python script with the actual ids algorithm
  - gets scap files via rest
  - does detection 
  - sends results to an other endpoint in json format, example: 
    {'generation': 'G1', 'testcases': [{'testcase': 'T001', 'anomaly-score-max': 0}]}

## rest-test

  - a small python helper script to test the ids endpoints: start/stop generation/testcase

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
     - example: `sudo python3 agent.py happy_agnesi http://127.0.0.1:80/ids/upload_scap`

## IDS
   - install sysdig into the ids machine, see: https://github.com/draios/sysdig/wiki/How-to-Install-Sysdig-for-Linux
   - move to ids directory
   - install python dependencies: `sudo pip install -r requirements.txt`
      - run the ids script: `sudo python3 ids.py [training|detection] path_to_model fuzzino_endpoint`
        - example: `sudo python3 ids.py training ./model.dat http://127.0.0.1:8081/fz/scores`

# Rest Enpoints and Communication Information

## Agent
- sends scap files via HTTP POST to the ids

## IDS
- recieves scap files over HTTP POST (/ids/upload_scap)
- recieves generation start events over HTTP POST (/ids/start_generation)
  - format json, example: `{"generation_name": "g-001"}`
- recieves generation stop events over HTTP POST (/ids/stop_generation)
  - format json, example: `{"generation_name": "g-001"}`
- recieves test case start events over HTTP POST (/ids/start_testcase)
  - format json, example: `{"testcase_name": "t-1"}`
- recieves test case stop events over HTTP POST (/ids/stop_testcase)
  - format json, example: `{"testcase_name": "t-1"}`
- sends generation and testcase results via HTTP POST 
  - format: json, example: `{'generation': 'G1', 'testcases': [{'testcase': 'T001', 'anomaly-score-max': 0}]}`
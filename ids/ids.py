import threading
import sys
import os
import requests

from flask import Flask, request
from werkzeug.utils import secure_filename
from watchdog.observers import Observer

import ids_helper as ids_helper
from ids_file_observer import ParserFileHandler
from testcases import TestcaseManager, Testcase

# some global variables:
observer = Observer()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getcwd() + "/uploads/"

# these three are used as global variables across the whole application (also in flask threads)
testcases = TestcaseManager()
current_generation = None
fuzzino_endpoint = None
mode = None
path_to_model_file = None
algorithm = None
features = None


# for uploading the files to the ids
@app.route('/ids/upload_scap', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "no file in request", 400

    file = request.files['file']
    if file.filename == '':
        return 'no file_name in request', 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return 'file sucessfull uploaded!', 200

@app.route('/ids/start_testcase', methods=['POST'])
def start_testcase():
    # accepts requests with json data like:
    # {
    # "testcase_name": "t-007",
    # }
    global testcases

    result = testcases.add_testcase_from_json(request.json)
    # print(request.json)
    if result:
        return f"testcase accepted", 200
    else:  
        return f"testcase already exists", 400

@app.route('/ids/stop_testcase', methods=['POST'])
def stop_testcase():
    # accepts requests with json data like:
    # {
    # "testcase_name": "t-007",
    # }
    global testcases

    result = testcases.end_testcase_from_json(request.json)
    # print(request.json)
    if result:
        return "testcase accepted", 200
    else:
        return "testcase not found", 400

@app.route('/ids/start_generation', methods=['POST'])
def start_generation():
    # accepts requests with json data like:
    # {
    # "generation_name": "g-001",
    # }
    global current_generation

    if current_generation is None:
        current_generation = request.json["generation_name"]
        if current_generation:
            return f"generation \"{current_generation}\" accepted", 200
        else:  
            return f"no name for generation given", 400
    else:
        return f"generation \"{current_generation}\" already running", 400
    

@app.route('/ids/stop_generation', methods=['POST'])
def stop_generation():
    # accepts requests with json data like:
    # {
    # "generation_name": "g-001",
    # }
    global current_generation

    if request.json["generation_name"] and request.json["generation_name"] == current_generation:
        evaluate_generation()
        current_generation = None
        return f"generation ended and data send", 200
    else:  
        return f"no name for generation given or the given generation wasnt active", 400



# for the file observer / ids 
def run_observer():    
    # ParserFileHandler
    global mode
    global path_to_model_file
    global algorithm
    global features

    path = os.getcwd() + "/uploads/"
    print(f"[IDS] observing files in: {path}")
    event_handler = ParserFileHandler(testcases, mode, path_to_model_file, algorithm, features)
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    

def evaluate_generation():
    ## send the generation results to the fuzzino server
    ## format json, example: {'generation': 'G1', 'testcases': [{'testcase': 'T001', 'anomaly-score-max': 0}]}


    global current_generation
    global testcases
    global fuzzino_endpoint

    # evaluate the current generation
    result_data = {}
    result_data["generation"] = current_generation
    result_data["testcases"] = []
    for testcase in testcases._testcases.values():
        # evaluate the testcase
        result_data["testcases"].append({"testcase":testcase._name, "anomaly-score-max":testcase._max_score})
    # send the results to the server
    print(f"[IDS] sending results to {fuzzino_endpoint}")
    print(f"[IDS] data send: ")
    print("[IDS] ---------------------")
    print(f"[IDS] {result_data}")
    print("[IDS] ---------------------")
    
    try:
        response = requests.post(fuzzino_endpoint, json=result_data)
        response.raise_for_status()
        print(f"[IDS] fuzzino response code: {response.status_code}")
        print(f"[IDS] fuzzino response text: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[IDS] error: {e}")

    # finally create a new testcase manager
    testcases = TestcaseManager()

###########################################################################
# START
###########################################################################
if __name__ == "__main__":
    # check for command line arguments
    # first argument: ids-mode (training/detection) 
    #   training  -> do training
    #   detection -> do detection
    # second argument: path to ids-model-file
    #   in training:  save model to file
    #   in detection: load model from file
    # third argument: hostname to listen or None
    # fourth argument: port to listen or None
    # fifth argument: fuzzino-endpoint

    # check for arguments
    needed_arguments = "needed arguments: [training|detection] path_to_model_file algorithm features hostname port fuzzino_endpoint"
    algorithm_list = ["astide", "fstide"]
    features_list = ["name", "name_result"]
    if len(sys.argv) == 8:
        mode = sys.argv[1]
        if mode != "training" and mode != "detection":
            print("[IDS] mode has to be \"training\" or \"detection\"")
            print(needed_arguments)
            exit()        
        path_to_model_file = sys.argv[2]
        algorithm = sys.argv[3]
        if algorithm.lower() not in algorithm_list:
            print(f"[IDS] algorithm has to be from the following list: {algorithm_list}")
        features = sys.argv[4]
        if features not in features_list:
            print(f"[IDS] features has to be from the following list: {features_list}")
        hostname_to_listen = sys.argv[5]
        port_to_listen = sys.argv[6]        
        fuzzino_endpoint = sys.argv[7]
    else:
        print(needed_arguments)
        print(f"algorithm options: {algorithm_list}")
        print(f"feature options: {features_list}")
        exit()

    # run the file observer part
    t = threading.Thread(target=run_observer)
    t.start()

    # run server for upload handling
    app.run(host=hostname_to_listen, port=port_to_listen, debug=False)
    print("[IDS] flask server ended...")

    # at the end, close the other threads
    ids_helper.close_thread(t,"observer helper")
    ids_helper.close_thread(observer, "observer")

import threading
import sys
import os

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
testcases = TestcaseManager()




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

    result = testcases.end_testcase_from_json(request.json)
    # print(request.json)
    if result:
        return "testcase accepted", 200
    else:
        return "testcase not found", 400



# for the file observer / ids 
def run_observer():
    # ParserFileHandler
    path = os.getcwd() + "/uploads/"
    print(f"[IDS] observing files in: {path}")
    event_handler = ParserFileHandler(testcases)
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    

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

    # Überprüfen Sie, ob Argumente übergeben wurden
    if len(sys.argv) > 1:        
        pass
    else:
        exit()

    # run the file observer part
    t = threading.Thread(target=run_observer)
    t.start()

    # run server for upload handling
    app.run(port=80, debug=False)
    print("[IDS] flask server ended...")

    # at the end, close the other threads
    ids_helper.close_thread(t,"observer helper")
    ids_helper.close_thread(observer, "observer")

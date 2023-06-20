import subprocess
import signal
import time
import sys
import requests
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from syscall import Syscall
from astide import ASTIDE

def handle_interrupt(signal, frame):
    print("ctrl + c detected -> ending")
    observer.stop()
    observer.join()
    exit(0)

# Handles file observer and starts parsing the files
class ParserFileHandler(FileSystemEventHandler):
    def __init__(self):        
        self._files = set()
        self._stide = ASTIDE()        

    def on_modified(self, event):        
        filename = os.path.basename(event.src_path)
        if not event.is_directory and filename.startswith('trace.scap') and filename[10:].isdigit():            
            if event.src_path not in self._files:
                print(f'waiting for file: {event.src_path} ... ',end='', flush=True)
                self._files.add(event.src_path) # remove this entry when detection is done on it
                self.wait_and_parse(event.src_path)

    def wait_and_parse(self, file_path):
        size_prev = -1
        while size_prev != os.path.getsize(file_path):
            size_prev = os.path.getsize(file_path)
            time.sleep(1)  # wait a second and check the size again
        self.parse_file(file_path)

    def parse_file(self, file_path):
        print(f"parsing file: {file_path} ...")
        self._parse_sysdig_output(file_path)
        self.delete_file(file_path)
    
    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"done and sucessfully deleted.")
        except OSError as e:
            print(f"Error trying do delete: {file_path} : {e.strerror}")

    def _parse_sysdig_output(self, file_path):
        max_score = 0
        with subprocess.Popen(["sysdig", "-r", file_path, "-p", "%evt.rawtime %proc.name %thread.tid %evt.dir %syscall.type %evt.args"], stdout=subprocess.PIPE) as proc:
            for line in proc.stdout:
                # line enthält eine Zeile der Ausgabe
                line = line.decode('utf-8').strip()  # decode and remove leading and trailing whitespace
                # print(line)
                current_syscall = Syscall(line)
                if self._stide.mode == "training":
                    self._stide.train_on(current_syscall)
                else:
                    current_score = self._stide.get_score(current_syscall)
                    if current_score is not None:
                        max_score = max(current_score, max_score)
        if self._stide.mode == "training":
            self._stide.fit()
        if self._stide.mode == "detection":
            print(f"max anomaly score for the last file: {max_score}")

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

    # ParserFileHandler
    path = os.getcwd() + "/uploads/"
    print(f"observing files in: {path}")
    event_handler = ParserFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        while True:
            time.sleep(1)
    except: 
        pass

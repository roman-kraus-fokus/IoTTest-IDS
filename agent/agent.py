import subprocess
import signal
import time
import sys
import requests
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Signal-Handler
def handle_signal(sig, frame):
    sysdig_process.terminate()
    sysdig_process.wait()
    sys.exit(0)

# register signal handler
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# Handles file observer and sends the files to IDS
class AgentFileHandler(FileSystemEventHandler):
    def __init__(self, endpoint):        
        self._endpoint = endpoint
        self._sent_files = set()

    def on_modified(self, event):
        #print(f"modified event: {event}")
        filename = os.path.basename(event.src_path)
        if not event.is_directory and filename.startswith('trace.scap') and filename[10:].isdigit():            
            if event.src_path not in self._sent_files:
                print(f'waiting for file: {event.src_path} ... ',end='', flush=True)
                self._sent_files.add(event.src_path)
                self.wait_and_send(event.src_path)

    def wait_and_send(self, file_path):
        size_prev = -1
        while size_prev != os.path.getsize(file_path):
            size_prev = os.path.getsize(file_path)
            time.sleep(1)  # wait a second and check the size again
        self.send_file(file_path)

    def send_file(self, file_path):        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            try:
                print('sending ... ', end='', flush=True)
                r = requests.post(self._endpoint, files=files)
                r.raise_for_status()                
            except requests.exceptions.RequestException as e:
                print(f'error {file_path}: {e}')
        self.delete_file(file_path)
    
    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"done and sucessfully deleted.")
        except OSError as e:
            print(f"Error trying do delete: {file_path} : {e.strerror}")


###########################################################################
# START
###########################################################################
if __name__ == "__main__":
    # check for command line arguments
    # we want the name of the container to observe on position 1

    # Überprüfen Sie, ob Argumente übergeben wurden
    if len(sys.argv) > 1:        
        target_container = sys.argv[1]
        print(f"Container Name: {target_container}")
        endpoint = sys.argv[2]
        print(f"Endpoint: {endpoint}")
    else:
        print("need arguments: container_name endpoint")
        exit()

    # AgentFileHandler
    path = os.getcwd() + "/recordings/"
    print(f"observing files in: {path}")
    event_handler = AgentFileHandler(endpoint=endpoint)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    # start Sysdig as background process
    # -G 10 -> new file each 10 seconds
    # -w trace.scap -> filename for the files
    # -W 6 -> automatic file rotation, max 6 files
    sysdig_process = subprocess.Popen(["sysdig", "-G", "10", "-w", "recordings/trace.scap", f"container.name={target_container}"])

    try:
        print("agent is recording system calls and sending files to the given endpoint...")
        print("--> press ctrl+c to stop agent <--")        
        while True:
            time.sleep(1)

    finally:
        # stop the observer
        observer.stop()
        # wait for observer 
        observer.join()
        # stop Sysdig, when this script terminates        
        sysdig_process.send_signal(signal.SIGTERM)
        sysdig_process.wait()
        print("agent stopped.")

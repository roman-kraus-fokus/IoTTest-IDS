import subprocess
import signal
import time
import sys
import requests
import os
from datetime import datetime
from queue import Queue

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Signal-Handler
def handle_signal(sig, frame):
    sysdig_process.terminate()
    sysdig_process.wait()
    sys.exit(0)

def get_current_timestamp():
    """Returns the current system timestamp in a human-readable format"""
    return datetime.today().strftime('%Y-%m-%d %H:%M:%S')

def start_sysdig(target_container: str):
    """Starts a sysdig process for monitoring the Docker container with the given name"""
    return subprocess.Popen(["sysdig", "-G", "10", "-w", "recordings/trace.scap", f"container.name={target_container}"])

# register signal handler
signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# Handles file observer and sends the files to IDS
class AgentFileHandler(FileSystemEventHandler):
    def __init__(self, endpoint):        
        self._endpoint = endpoint
        self._sent_files = set()
        self.last_update_timestamp = time.time()  # Timestamp of the last update in seconds
        self.file_queue = Queue()  # Queue of files to send

    def on_modified(self, event):
        #print(f"modified event: {event}")
        filename = os.path.basename(event.src_path)
        if not event.is_directory and filename.startswith('trace.scap') and filename[10:].isdigit():            
            if event.src_path not in self._sent_files:
                print(f'[{get_current_timestamp()}] Registered file: {event.src_path}', flush=True)
                self._sent_files.add(event.src_path)
                self.file_queue.put(event.src_path)
                self.send_next_waiting_file()

    def send_next_waiting_file(self):
        if self.file_queue.qsize() <= 1:
            # We send file i only once file i + 1 has arrived
            # This way we know that file i has been completely written to disk
            return
        file_path = self.file_queue.get_nowait()
        self.send_file(file_path)
        self.last_update_timestamp = time.time()
        return

    def send_file(self, file_path):        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            try:
                print(f'[{get_current_timestamp()}] sending {file_path} ', end='', flush=True)
                r = requests.post(self._endpoint, files=files)
                r.raise_for_status()                
            except requests.exceptions.RequestException as e:
                print(f'[{get_current_timestamp()}] Error {file_path}: {e}', flush=True)
        self.delete_file(file_path)
    
    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"[{get_current_timestamp()}] done and sucessfully deleted.", flush=True)
        except OSError as e:
            print(f"[{get_current_timestamp()}] Error trying do delete: {file_path} : {e.strerror}", flush=True)

    def is_hanging(self):
        """Returns true if it is suspected that the processing is hanging"""
        return (time.time() - self.last_update_timestamp) > (20 * 1_000)

    def restart(self):
        print(f"[{get_current_timestamp()}] Restarting!", flush=True)
        self.last_update_timestamp = time.time()
        self._sent_files = set()


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

    
    path = os.getcwd() + "/recordings/"
    # first check wether the directory already exists, if not create it
    if not os.path.exists(path):
        os.makedirs(path)

    # AgentFileHandler
    print(f"observing files in: {path}")
    event_handler = AgentFileHandler(endpoint=endpoint)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    # start Sysdig as background process
    # -G 10 -> new file each 10 seconds
    # -w trace.scap -> filename for the files
    # -W 6 -> automatic file rotation, max 6 files
    # old variant
    sysdig_process = start_sysdig(target_container)
    # new for default model generation only records mosquitto processes
    # sysdig_process = subprocess.Popen(["sysdig", "-G", "10", "-w", "recordings/trace.scap", f"(container.name={target_container} and proc.name=mosquitto)"])

    try:
        print("agent is recording system calls and sending files to the given endpoint...")
        print("--> press ctrl+c to stop agent <--")        
        while True:
            time.sleep(1)
            if sysdig_process.poll() is not None:
                print(f"[{get_current_timestamp()}] Restarting Sysdig as process seems finished...")
                # Stopping the observer thread
                observer.stop()
                observer.join()
                # Restarting the observer and event handler
                observer = Observer()
                event_handler.restart()
                observer.schedule(event_handler, path, recursive=False)
                observer.start()
                # Restarting sysdig
                sysdig_process = start_sysdig(target_container)
            elif event_handler.is_hanging():
                print(f"[{get_current_timestamp()}] Restarting Sysdig because the process is hanging...")
                os.killpg(os.getpgid(sysdig_process.pid), signal.SIGTERM)
                sysdig_process = start_sysdig(target_container)
                event_handler.restart()

    finally:
        # stop the observer
        observer.stop()
        # wait for observer 
        observer.join()
        # stop Sysdig, when this script terminates        
        sysdig_process.send_signal(signal.SIGTERM)
        sysdig_process.wait()
        print("agent stopped.")

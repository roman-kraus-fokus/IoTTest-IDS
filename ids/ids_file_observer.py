import subprocess
import time

import os
from watchdog.events import FileSystemEventHandler

from syscall import Syscall
from astide import ASTIDE
from fstide import FSTIDE
from stats import Stats
from queue import Queue

# Handles file observer and starts parsing the files
class ParserFileHandler(FileSystemEventHandler):
    def __init__(self, testcase_manager, mode, path_to_model_file, algorithm, features):        
        self._files = set()
        self.file_queue = Queue()  # Queue of files to process
        if algorithm.lower() == "astide":
            self._stide = ASTIDE(mode=mode, model_file=path_to_model_file)
        if algorithm.lower() == "fstide":
            self._stide = FSTIDE(mode=mode, model_file=path_to_model_file, syscall_mapper=features)

        self._testcase_manager = testcase_manager

    def on_modified(self, event):        
        filename = os.path.basename(event.src_path)
        if not event.is_directory and filename.startswith('trace.scap') and filename[10:].isdigit():            
            if event.src_path not in self._files:
                print(f'[FileHandler] ------------------------------------------ ', flush=True)
                print(f'[FileHandler] Receiving file: {event.src_path}', flush=True)
                self._files.add(event.src_path) # remove this entry when detection is done on it
                self.file_queue.put(event.src_path)
                self.parse_next_waiting_file()

    def parse_next_waiting_file(self):
        if self.file_queue.qsize() <= 1:
            # We send file i only once file i + 1 has arrived
            # This way we know that file i has been completely written to disk
            return
        file_path = self.file_queue.get_nowait()
        self.parse_file(file_path)

    def parse_file(self, file_path):
        print(f"[FileHandler] parsing file: {file_path}", flush=True)
        self._parse_sysdig_output(file_path)
        self.delete_file(file_path)
    
    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            self._files.remove(file_path)
            print(f"[FileHandler] done and sucessfully deleted.", flush=True)
        except OSError as e:
            print(f"[FileHandler] Error trying do delete: {file_path} : {e.strerror}", flush=True)

    def _parse_sysdig_output(self, file_path):
        stats = Stats()
        current_syscall = None
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
                        stats.add_value(current_score)
                        # Getting all testcases which match time timestamp of the syscall and adding the IDS score to them
                        testcase_list = self._testcase_manager.get_matching_testcases(current_syscall.timestamp_unix_in_ns()) 
                        if len(testcase_list) > 1:
                            print(f"[FileHandler] Associating IDS score with multiple test cases, namely {testcase_list}", flush=True)
                        for testcase in testcase_list:
                            testcase.add_score(current_score)
        if self._stide.mode == "training":
            self._stide.fit()
        elif self._stide.mode == "detection":
            print(f"[FileHandler] min/avg/max anomaly scores for the last file: {stats.get_min()}/{stats.get_average()}/{stats.get_max()}", flush=True)
            if current_syscall:
                print(f"[FileHandler] current testcase(s): {self._testcase_manager.get_matching_testcases(current_syscall.timestamp_unix_in_ns())}", flush=True)

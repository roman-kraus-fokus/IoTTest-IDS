import subprocess
import time

import os
from watchdog.events import FileSystemEventHandler

from syscall import Syscall
from astide import ASTIDE
from fstide import FSTIDE
from stats import Stats

# Handles file observer and starts parsing the files
class ParserFileHandler(FileSystemEventHandler):
    def __init__(self, testcase_manager, mode, path_to_model_file, algorithm, features):        
        self._files = set()
        if algorithm.lower() == "astide":
            self._stide = ASTIDE(mode=mode, model_file=path_to_model_file)
        if algorithm.lower() == "fstide":
            self._stide = FSTIDE(mode=mode, model_file=path_to_model_file, syscall_mapper=features)

        self._testcase_manager = testcase_manager

    def on_modified(self, event):        
        filename = os.path.basename(event.src_path)
        if not event.is_directory and filename.startswith('trace.scap') and filename[10:].isdigit():            
            if event.src_path not in self._files:
                print(f'[FileHandler] ------------------------------------------ ')
                print(f'[FileHandler] waiting for file: {event.src_path}')
                self._files.add(event.src_path) # remove this entry when detection is done on it
                self.wait_and_parse(event.src_path)

    def wait_and_parse(self, file_path):
        size_prev = -1
        while size_prev != os.path.getsize(file_path):
            size_prev = os.path.getsize(file_path)
            time.sleep(1)  # wait a second and check the size again
        self.parse_file(file_path)

    def parse_file(self, file_path):
        print(f"[FileHandler] parsing file: {file_path}")
        self._parse_sysdig_output(file_path)
        self.delete_file(file_path)
    
    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"[FileHandler] done and sucessfully deleted.")
        except OSError as e:
            print(f"[FileHandler] Error trying do delete: {file_path} : {e.strerror}")

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
                        testcase = self._testcase_manager.get_current_testcase(current_syscall.timestamp_unix_in_ns()) 
                        if testcase is not None:
                            testcase.add_score(current_score)
        if self._stide.mode == "training":
            self._stide.fit()
        elif self._stide.mode == "detection":
            print(f"[FileHandler] min/avg/max anomaly scores for the last file: {stats.get_min()}/{stats.get_average()}/{stats.get_max()}")
            print(f"[FileHandler] current testcase: {self._testcase_manager.get_current_testcase(current_syscall.timestamp_unix_in_ns())}")

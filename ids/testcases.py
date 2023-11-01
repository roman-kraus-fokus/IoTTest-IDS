
# a class which holds a list of testcases with name, start and end timestamp
# it should provide methods to add testcases and to get the current testcase based on a timestamp in milliseconds

import time
import threading

from ids_helper import timestamp_in_hh_mm_ss

class Testcase:
    def __init__(self, name, start, end=None):
        self._name = name
        self._start = start
        self._end = end
        self._max_score = 0
    
    def add_score(self, score):
        self._max_score = max(self._max_score, score)

    def __str__(self) -> str:
        return f"[TC: {self._name}, {timestamp_in_hh_mm_ss(self._start)} - {timestamp_in_hh_mm_ss(self._end)}, {self._max_score}]"


class SafeDict:
    def __init__(self):
        self._dict = {}
        self._lock = threading.Lock()

    def add(self, key, value):
        with self._lock:
            self._dict[key] = value

    def remove(self, key):
        with self._lock:
            if key in self._dict:
                del self._dict[key]

    def iterate_values(self):
        with self._lock:
            for value in self._dict.values():
                yield value
    
    def __contains__(self, key):
        with self._lock:
            return key in self._dict

    def size(self):
        with self._lock:
            return len(self._dict)        


class TestcaseManager:
    def __init__(self):
        self.reset()

    def reset(self):
        self._testcases = SafeDict()
        self._last_inserted_testcase = None
        self._current_testcase = None
    
    def get_current_testcase(self, timestamp): 
        if self._current_testcase is None:            
            if self._testcases.size() == 0:
                return None
            for testcase in self._testcases.iterate_values():
                if testcase._start <= timestamp:
                    if testcase._end is None or timestamp <= testcase._end:                    
                        self._current_testcase = testcase            
            return self._current_testcase
        else:        
            if self._current_testcase._end is None:            
                return self._current_testcase
            if self._current_testcase._end < timestamp:
                self._current_testcase = None            
                return self.get_current_testcase(timestamp)
        return None
        
    def _get_last_testcase(self):
        return self._last_inserted_testcase
    
    def _add_testcase(self, name, start, end=None):
        temp_testcase = Testcase(name, start, end)
        if self._get_last_testcase() is not None:
            if self._get_last_testcase()._end is None:
                self._get_last_testcase()._end = start-1
        self._testcases.add(name,temp_testcase)
        self._last_inserted_testcase = temp_testcase
        
    def _end_testcase(self , name, timestamp):
        temp_testcase = self._testcases._dict[name]
        temp_testcase._end = timestamp

    def add_testcase_from_json(self, json):
        if json["testcase_name"] in self._testcases:
            return False
        else:
            self._add_testcase(json["testcase_name"], time.time_ns())
            return True
        
    def end_testcase_from_json(self, json):
        if json["testcase_name"] in self._testcases:
            if self._testcases._dict[json["testcase_name"]]._end is not None:
                return False
            else:
                self._end_testcase(json["testcase_name"], time.time_ns())
                return True
        else:
            return False

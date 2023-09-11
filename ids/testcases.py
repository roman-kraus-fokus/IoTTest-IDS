
# a class which holds a list of testcases with name, start and end timestamp
# it should provide methods to add testcases and to get the current testcase based on a timestamp in milliseconds

import time
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


class TestcaseManager:
    def __init__(self):
        self.reset()

    def reset(self):
        self._testcases = {}
        self._last_inserted_testcase = None
        self._current_testcase = None
    
    def get_current_testcase(self, timestamp): 
        # print(f"> get_current_testcase({timestamp_in_hh_mm_ss(timestamp)})")
        if self._current_testcase is None:            
            # print the contents of the testcases dictionary
            # for testcase in self._testcases.values():
            #    print(f">> {testcase}")

            if len(self._testcases) == 0:
                # print("> no testcases")
                return None
            for testcase in self._testcases.values():
                if testcase._start <= timestamp:
                    if testcase._end is None or timestamp <= testcase._end:                    
                        self._current_testcase = testcase
            # print(f"> 1 current testcase: {self._current_testcase}")
            return self._current_testcase
        else:        
            if self._current_testcase._end is None:
                # print(f"> 2 current testcase: {self._current_testcase}")
                return self._current_testcase
            if self._current_testcase._end < timestamp:
                self._current_testcase = None
                # print(f"> 3 ...")
                return self.get_current_testcase(timestamp)
        # print("> None")
        return None
        
    def _get_last_testcase(self):
        return self._last_inserted_testcase
    
    def _add_testcase(self, name, start, end=None):
        # print(f"_add_testcase({name}, {start}, {end})")
        temp_testcase = Testcase(name, start, end)
        if self._get_last_testcase() is not None:
            # print(f"self._get_last_testcase() is not None")
            if self._get_last_testcase()._end is None:
                # print(f"self._get_last_testcase()._end is None")
                self._get_last_testcase()._end = start-1
        self._testcases[name] = temp_testcase
        self._last_inserted_testcase = temp_testcase
        # print(f"self._testcases[{name}] = {self._testcases[name]}")
        # print("last testcase: " + str(self._get_last_testcase()))
        # print("current testcase: " + str(self._current_testcase))
        # print("###########################################")
        
    def _end_testcase(self , name, timestamp):
        temp_testcase = self._testcases[name]
        temp_testcase._end = timestamp

    def add_testcase_from_json(self, json):
        if json["testcase_name"] in self._testcases:
            return False
        else:            
            self._add_testcase(json["testcase_name"], time.time_ns())
            return True
        
    def end_testcase_from_json(self, json):
        if json["testcase_name"] in self._testcases:            
            if self._testcases[json["testcase_name"]]._end is not None:
                return False
            else:
                self._end_testcase(json["testcase_name"], time.time_ns())
                return True
        else:
            return False

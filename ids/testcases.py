
# a class which holds a list of testcases with name, start and end timestamp
# it should provide methods to add testcases and to get the current testcase based on a timestamp in milliseconds



class Testcase:
    def __init__(self, name, start, end=None):
        self._name = name
        self._start = start
        self._end = end

    def __str__(self) -> str:
        return f"Testcase: {self._name} started at {self._start} and ended at {self._end}"


class TestcaseManager:
    def __init__(self):
        self._testcases = {}
        self._last_inserted_testcase = None
        self._current_testcase = None
    
    def get_current_testcase(self, timestamp): 
        if self._current_testcase is None:
            if len(self._testcases) == 0:
                return None
            for testcase in self._testcases:
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
        self._testcases[name] = temp_testcase
        
    def _end_testcase(self , name, timestamp):
        temp_testcase = self._testcases[name]
        temp_testcase._end = timestamp

    def add_testcase_from_json(self, json):
        if json["testcase_name"] in self._testcases:
            return False
        else:
            self._add_testcase(json["testcase_name"], json["timestamp_unix_in_ns"])
            return True
        
    def end_testcase_from_json(self, json):
        if json["testcase_name"] in self._testcases:
            self._end_testcase(json["testcase_name"], json["timestamp_unix_in_ns"])
            return True
        else:
            return False

    
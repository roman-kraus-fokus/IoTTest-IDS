
# a class which holds a list of testcases with name, start and end timestamp
# it should provide methods to add testcases and to get the current testcase based on a timestamp in milliseconds

import time
import threading

from ids_helper import timestamp_in_hh_mm_ss
from stats import Stats

class Testcase:
    def __init__(self, name, start, end=None):
        self._name = name
        self._start = start
        self._end = end
        self._max_score = 0
        self._has_score = False  # If True, it indicates that an IDS score has been set for this Testcase
        self._is_finished = False  # If True, it indicates that no more IDS scores will be added to this Testcase
        self._score_stats = Stats()

    def is_finished(self):
        return self._is_finished

    def set_is_finished(self, is_finished):
        self._is_finished = is_finished

    def has_score(self):
        return self._has_score
    
    def add_score(self, score):
        self._max_score = max(self._max_score, score)
        self._score_stats.add_value(score)
        self._has_score = True

    def get_avg_value(self):
        return self._score_stats.get_average()

    def __str__(self) -> str:
        return f"[TC: {self._name}, {timestamp_in_hh_mm_ss(self._start)} - {timestamp_in_hh_mm_ss(self._end)}, {self._max_score}]"

    def __repr__(self) -> str:
        # We overwrite this method so that we get a human-readable representation when printing a list containing a Testcase
        return self.__str__()


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

    def values(self):
        with self._lock:
            # Return a copy of the values to ensure thread safety
            # attention: this is in form of a list, but it shouldnt matter in most cases
            return list(self._dict.values())


class TestcaseManager:
    def __init__(self):
        self.reset()

    def is_complete(self):
        """Returns True if the IDS scores of all its Testcases are fixed (i.e., they won't change anymore)"""
        result = True
        for testcase in self._testcases.iterate_values():
            if not testcase.has_score() and not testcase.is_finished():
                print(f"Testcase {testcase} has no value yet!", flush=True)
                result = False
        return result

    def reset(self):
        self._testcases = SafeDict()
        self._last_inserted_testcase = None
        self._current_testcase = None

    def get_matching_testcases(self, timestamp):
        """Returns all Testcases of this TestcaseManager whose time window includes the given timestamp"""
        # TODO: If I am not mistaken, then there can be at max one test case which matches a given time stamp. So, the list might not be necessary.
        #  However, the iteration over all testcases here still makes sense to set testcases as 'finished' for which no more IDS updates are expected.
        test_case_list = []
        for testcase in self._testcases.iterate_values():
                # Making sure that the testcases starts before or at the given timestamp
                if testcase._start <= timestamp:
                    if testcase._end is None or timestamp <= testcase._end:
                        # We add the testcase if it does not have any defined end or if its end is after or at the given timestamp              
                        test_case_list.append(testcase)
                    elif testcase._end is not None and testcase._end < timestamp:
                        # If the testcase has a defined end and but it is smaller than the timestamp, then we assume that
                        # the IDS is already processing syscalls which happened after this testcase. This testcase will
                        # thus not receive any more updates from the IDS and we consider it finished 
                        testcase.set_is_finished(True)
        return test_case_list
        
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

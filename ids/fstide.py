from collections import deque
import time
import json
import math

from syscall import Syscall
from syscall import Direction
from angram import ANgram
from histogram import Histogram

# helper function: maps a given system call to its name
def name_r(syscall: Syscall):    
    r = ""
    if syscall.name() in ("read","write", "pread", "pwrite","readv","writev","preadv","pwritev", "sendfile", "splice"):
        r = syscall.param("res")    
        if r is None:
            r = ""
    return syscall.name() + r

def name(syscall: Syscall):    
    return syscall.name()

class FSTIDE():
    # Initialize FrequencySTIDE with given number of ngrams, window size, and early stopping time
    def __init__(self, mode="detection", n=9, w=500, es_training_seconds=30, syscall_mapper="name", model_file="models/mosquitto_default.json"):

        # Set the ngram number
        self._n = n
        # Set the window size
        self._w = w

        if syscall_mapper == "name":
            self._syscall_mapper = name
        if syscall_mapper == "name_result":
            self._syscall_mapper = name_r

        # current operating mode
        self.mode = mode

        # model file
        self._model_file = model_file
        
        # Set the training syscall counter and ngram counter
        self._seen_training_syscalls = 0
        self._seen_training_ngrams = 0

        # Set the early stopping value 
        self._early_stopping_seconds = es_training_seconds
        self._early_stopping_last_modification_ts = 0
        self._early_stopping_last_seen_ts = 0

        # Initialize an empty set to hold normal syscall ngrams
        self._normal_database = Histogram()
        self._alpha = 0.01
        
        # Initialize an empty deque to hold the scores buffer within the sliding window
        self._window_score_buffer = deque(maxlen=self._w)
        # Initialize a counter for the number of scores in the sliding window
        self._sum_of_scores_in_window = 0

        # Initialize an ngram builder with a specific ngram number
        self._ngram_builder = ANgram(n)

        if self.mode == "detection":
            print(f"[FreqSTIDE] started in detection mode...")
            self.from_json_file(self._model_file)
        else:
            print(f"[FreqSTIDE] started in training mode...")

    # Method to train on a given syscall, generating unique ngrams and storing them in the normal_database set
    def train_on(self, syscall: Syscall):
        """
        creates a set for distinct ngrams from training data
        """
        self._seen_training_syscalls += 1
        self._early_stopping_last_seen_ts = syscall.timestamp_unix_in_ns() / 1_000_000_000
        # Generate an ngram from the syscall
        ngram = self._ngram_builder.get_ngram(syscall, self._syscall_mapper)
        if ngram is not None:
            self._seen_training_ngrams += 1
            # add the ngram to the database (increment its count)
            self._normal_database.add(ngram)
            # if this was a new ngram, update the early stopping timestamp
            if self._normal_database.get_count(ngram) == 1:
                self._early_stopping_last_modification_ts = syscall.timestamp_unix_in_ns() / 1_000_000_000

    # Method to reset the window scores buffer and the counter for number of scores
    def reset_buffer(self):
        # Reset the scores buffer
        self._window_score_buffer = deque(maxlen=self._w)
        # Reset the number of scores
        self._sum_of_scores_in_window = 0 

    # Method to finalize the training (currently prints the current size of the training set)
    def fit(self):        
        # print(self._normal_database)        
        print(f"[FreqSTIDE] FreqStide.seen_syscalls in training: {self._seen_training_syscalls}")
        print(f"[FreqSTIDE] FreqStide.seen_ngrams in training  : {self._seen_training_ngrams}")
        print(f"[FreqSTIDE] FreqStide.unique_elements          : {self._normal_database.unique_elements()}")
        # print(self._normal_database)        
        self.to_json_file(self._model_file)
        
        dt = self._early_stopping_last_seen_ts - self._early_stopping_last_modification_ts
        print(f"[FreqSTIDE] time since last unique datapoint: {dt} seconds ")
        if dt >= self._early_stopping_seconds:
            # training done...
            print("[FreqSTIDE] training done -> switch to detection")
            self.mode = "detection"
            

    # Helper function to determine the score of a given ngram
    def _get_score(self, ngram: tuple):
        """
        calculates the score for a given ngram
        """       
        if ngram in self._normal_database:
            ngram_freq = self._normal_database.get_count(ngram)
        else:
            ngram_freq = 0
        # return math.pow(self._alpha, ngram_freq)
        return math.exp(-self._alpha * ngram_freq)

    # Method to calculate the sum of scores within the current sliding window of syscalls
    def get_score(self, syscall: Syscall):
        """
        calculates sum of scores of ngrams in sliding window of current recording
        """
        # Generate an ngram from the syscall
        ngram = self._ngram_builder.get_ngram(syscall, self._syscall_mapper)
        if ngram is not None:            
            # Determine the ngram score
            score = self._get_score(ngram)

            # Get the oldest value in the window
            oldest_value = 0
            if len(self._window_score_buffer) == self._w:
                oldest_value = self._window_score_buffer[0]
            
            # Add the current score to the buffer
            self._window_score_buffer.append(score)
            # Adjust the sum of scores based on the oldest value
            self._sum_of_scores_in_window += score - oldest_value
            
            # If the window is full, return the sum of scores
            if len(self._window_score_buffer) == self._w:
                return self._sum_of_scores_in_window / self._w
        
        # If no ngram could be generated or the window is not full, return None
        return None
    
    def to_json_file(self, file_name):
        """
        saves the current model to a json file
        """
        # print(self._normal_database._counts)
        # convert tuple(str) keys to json compatible str:
        data_str_keys = {json.dumps(key): value for key, value in self._normal_database._counts.items()}

        with open(file_name, 'w') as outfile:
            json.dump(data_str_keys, outfile, indent=4)
            print(f"[FreqSTIDE] model saved to {file_name}")

    def from_json_file(self, file_name):
        """
        loads a model from a json file
        """
        with open(file_name) as json_file:
            data_str_keys = json.load(json_file)            
            # Convert string keys back to tuple keys
            # data = {tuple(json.loads(key)): value for key, value in data_str_keys.items()}
            self._normal_database = Histogram()
            for key, value in data_str_keys.items():
                self._normal_database.add(tuple(json.loads(key)),value)
            print(f"[FreqSTIDE] model loaded from {file_name}")
            print(f"[FreqSTIDE] unique_elements: {self._normal_database.unique_elements()}")

from collections import deque
import time

from syscall import Syscall
from angram import ANgram

# helper function: maps a given system call to its name
def name(syscall: Syscall):
    return syscall.name()

# helper function: maps a given system call to its name
def name_ret(syscall: Syscall):
    ret = syscall.param("ret")
    if ret is None:
        return syscall.name()
    else:
        return syscall.name() + ret


class ASTIDE():
    # Initialize ASTIDE with given number of ngrams, window size, and early stopping time
    def __init__(self, n=5, w=500, es_training_seconds=30, syscall_mapper=name):

        # Set the ngram number
        self._n = n
        # Set the window size
        self._w = w

        self._syscall_mapper = syscall_mapper

        # current operating mode
        self.mode = "training"
        
        # Set the training syscall counter and ngram counter
        self._seen_training_syscalls = 0
        self._seen_training_ngrams = 0

        # Set the early stopping value 
        self._early_stopping_seconds = es_training_seconds
        self._early_stopping_last_modification_ts = 0
        self._early_stopping_last_seen_ts = 0

        # Initialize an empty set to hold normal syscall ngrams
        self._normal_database = set()
        
        # Initialize an empty deque to hold the mismatch buffer within the sliding window
        self._window_mismatch_buffer = deque(maxlen=self._w)
        # Initialize a counter for the number of mismatches in the sliding window
        self._number_of_mismatches_in_window = 0

        # Initialize an ngram builder with a specific ngram number
        self._ngram_builder = ANgram(n)

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
            # If the ngram is not already in the normal database, add it
            if ngram not in self._normal_database:
                self._normal_database.add(ngram)
                self._early_stopping_last_modification_ts = syscall.timestamp_unix_in_ns() / 1_000_000_000

    # Method to reset the window mismatch buffer and the counter for number of mismatches
    def reset_buffer(self):
        # Reset the mismatch buffer
        self._window_mismatch_buffer = deque(maxlen=self._w)
        # Reset the number of mismatches
        self._number_of_mismatches_in_window = 0 

    # Method to finalize the training (currently prints the current size of the training set)
    def fit(self):        
        # print(self._normal_database)
        print(f"[ASTIDE] astide.seen_syscalls in training: {self._seen_training_syscalls}")
        print(f"[ASTIDE] astide.seen_ngrams in training  : {self._seen_training_ngrams}")
        print(f"[ASTIDE] astide.train_set                : {len(self._normal_database)}")
        
        dt = self._early_stopping_last_seen_ts - self._early_stopping_last_modification_ts
        print(f"[ASTIDE] time since last model change: {dt} seconds ")
        if dt >= self._early_stopping_seconds:
            # training done...
            print("[ASTIDE] training done -> switch to detection")
            self.mode = "detection"

    # Helper function to determine if a given ngram is a mismatch
    def _is_mismatch(self, ngram: tuple):
        """
        calculates whether the given ngram is a match (0) or mismatch (1)
        """       
        # If the ngram is in the normal database, it's a match, otherwise it's a mismatch
        if ngram in self._normal_database:
            return 0
        else:
            return 1

    # Method to calculate the mismatch ratio within the current sliding window of syscalls
    def get_score(self, syscall: Syscall):
        """
        calculates ratio of unknown ngrams in sliding window of current recording
        """
        # Generate an ngram from the syscall
        ngram = self._ngram_builder.get_ngram(syscall, self._syscall_mapper)
        if ngram is not None:            
            # Determine if the ngram is a mismatch
            mismatch = self._is_mismatch(ngram)

            # Get the oldest value in the window
            oldest_value = 0
            if len(self._window_mismatch_buffer) == self._w:
                oldest_value = self._window_mismatch_buffer[0]
            
            # Add the current mismatch status to the buffer
            self._window_mismatch_buffer.append(mismatch)
            # Adjust the number of mismatches based on the oldest value
            self._number_of_mismatches_in_window += mismatch - oldest_value
            
            # If the window is full, calculate the mismatch/match ratio, and return it
            if len(self._window_mismatch_buffer) == self._w:
                return self._number_of_mismatches_in_window / self._w            
        
        # If no ngram could be generated or the window is not full, return None
        return None
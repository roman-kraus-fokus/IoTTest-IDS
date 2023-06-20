from typing import Callable
from collections import deque
from syscall import Syscall

class ANgram():
    """
    calculate thread aware ngram form a stream of system calls
    """

    def __init__(self, n: int):
        """
        n: length of the ngram
        """
        self._ngram_buffer = {}
        self._n = n

    def get_ngram(self, syscall: Syscall, element: Callable[[Syscall], str]):
        """
        builds ngrams from given system calls
        returns None if the ngrams are not full
        otherwise returns a tuple of length n (the ngram) of strings
        """        
        # group by thread id
        thread_id = syscall.thread_id()
        if thread_id not in self._ngram_buffer:
            self._ngram_buffer[thread_id] = deque(maxlen=self._n)
        
        # append the current element (generated from the syscall) to the ngram
        self._ngram_buffer[thread_id].append(element(syscall))

        # return the ngram if its complete
        if len(self._ngram_buffer[thread_id]) == self._n:
            return tuple(self._ngram_buffer[thread_id])
        return None

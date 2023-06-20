
from enum import IntEnum
from datetime import datetime

class Direction(IntEnum):
    OPEN = 0
    CLOSE = 1
    BOTH = 2

class Param(IntEnum):
    NAME = 0
    VALUE = 1

class SyscallSplitPart(IntEnum):
    TIMESTAMP = 0
    PROCESS_NAME = 1
    THREAD_ID = 2
    DIRECTION = 3
    SYSCALL_NAME = 4    
    PARAMS_BEGIN = 5  # use [SyscallSplitPart.PARAMS_BEGIN:] to retrieve all args as list

class Syscall:
    def __init__(self, syscall_line):        
        self._line_list = syscall_line.split(' ')        
        self._timestamp_unix = None
        self._timestamp_datetime = None        
        self._process_name = None
        self._thread_id = None
        self._name = None
        self._direction = None
        self._params = None

    def timestamp_unix_in_ns(self) -> int:
        """

        casts unix timestamp from string to int

        Returns:
            int: unix timestamp of syscall

        """
        if self._timestamp_unix is None:
            self._timestamp_unix = int(self._line_list[SyscallSplitPart.TIMESTAMP])

        return self._timestamp_unix

    def timestamp_datetime(self) -> datetime:
        """

        casts unix timestamp from string to python datetime object

        Returns:
            datetime: casted datetime object of syscall timestamp

        """
        if self._timestamp_datetime is None:
            self._timestamp_datetime = datetime.fromtimestamp(
                int(self._line_list[SyscallSplitPart.TIMESTAMP]) * 10 ** -9)

        return self._timestamp_datetime

    def process_name(self) -> str:
        """

        extracts process name

        Returns:
            string: process Name

        """
        if self._process_name is None:
            self._process_name = self._line_list[SyscallSplitPart.PROCESS_NAME]

        return self._process_name

    def thread_id(self) -> int:
        """

        casts thread_id from string to int

        Returns:
            int: thread id

        """
        if self._thread_id is None:
            self._thread_id = int(self._line_list[SyscallSplitPart.THREAD_ID])

        return self._thread_id

    def name(self) -> str:
        """

        gets syscall name from recorded line

        Returns:
            string: syscall name

        """
        if self._name is None:
            self._name = self._line_list[SyscallSplitPart.SYSCALL_NAME]

        return self._name

    def direction(self) -> Direction:
        """

        sets direction based on chars '<' and '>', casts to OPEN/CLOSE in enum

        Returns:
            Direction: the direction of the syscall

        """
        if self._direction is None:
            dir_char = self._line_list[SyscallSplitPart.DIRECTION]
            if dir_char == '>':
                self._direction = Direction.OPEN
            elif dir_char == '<':
                self._direction = Direction.CLOSE

        return self._direction

    def params(self) -> dict:
        """

        extracts params from param list and saves its names and values as dict

        Returns:
            dict: the syscalls parameters

        """
        if self._params is None:
            self._params = {}
            if len(self._line_list) > 5:  # check if params are given
                for param in self._line_list[SyscallSplitPart.PARAMS_BEGIN:]:
                    split = param.split('=', 1)
                    try:
                        self._params[split[Param.NAME]] = split[Param.VALUE]
                    except:
                        pass
        return self._params

    def param(self, param_name: str) -> str:
        """

        runs the params() method and returns the requested        

        Returns:
            str or bytes: syscall parameter value or None if param not available


        """
        params = self.params()
        try:
            param_value = params[param_name]
            return param_value
        except KeyError:
            return None
            

    def __str__(self):
        return f"[{self.name()}, {self.direction()}, {self.params()}]"

import datetime
import threading
import json
from multiprocessing import Queue, Value
import concurrent
import asyncio
from typing import Union

_logger = None


def get_logger():
    global _logger

    if _logger is None:
        _logger = DataLogger()

    return _logger


class Counter:
    ''' Multiprocessing safe counter for message id's
    '''

    def __init__(self):
        self.val = Value('i', 0)

    def __iadd__(self, n):
        with self.val.get_lock():
            self.val.value += n

        return self

    @property
    def value(self):
        return self.val.value


class DataPoint:
    # NOTE: if field access is regularly needed, this could straightforwardly
    # inherit from dict or implement __get/setitem__
    # NOTE: note multiprocessing safe
    id_counter = Counter()
    thread_lock = threading.Lock()

    def __init__(self, time=None, **kwargs):
        self.data = kwargs
        self.time = time or datetime.datetime.now(datetime.timezone.utc)

        with self.thread_lock:
            self.id = self.id_counter.value
            DataPoint.id_counter += 1

    def __str__(self):
        return json.dumps(
            {
             "time": self.time.timestamp() if isinstance(self.time, datetime.datetime) else self.time,
             "data": self.data,
             "id":   self.id
            },
        )


class DataLogger:
    def __init__(self):
        # use multiprocessing Queue so that
        # classifier can run in separate process
        self.data_queue = Queue()

        # auto create with timestamp
        self.filename = ""

    def __del__(self):
        # flush the queue
        self._write()

    def log(self, message: Union[DataPoint, dict]):
        if isinstance(message, DataPoint):
            data = message
        elif isinstance(message, dict):
            data = DataPoint(**message)
        else:
            raise Exception("Message format not supported")

        self.data_queue.put(data)

    def _write(self):
        with open(self.filename, 'a') as f:
            while not self.data_queue.empty():
               f.write(self.data_queue.get_nowait())

    async def write(self):
        '''
        :return: None
        '''
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await asyncio.run_in_executor(executor, self._write)

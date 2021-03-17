import datetime
import time
import json
from nicls.configuration import Config
from multiprocessing import Queue, Value
import concurrent
import asyncio
from typing import Union
import os
import logging

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

    def GrabAndIncrement(self):
        with self.val.get_lock():
            v = self.val.value
            self.val.value += 1
            return v


class DataPoint:
    # NOTE: if field access is regularly needed, this could straightforwardly
    # inherit from dict or implement __get/setitem__
    # NOTE: note multiprocessing safe
    id_counter = Counter()

    def __init__(self, time=None, **kwargs):
        self.data = kwargs
        self.time = time or datetime.datetime.now(datetime.timezone.utc)

        self.id = self.id_counter.GrabAndIncrement()

    def __str__(self):
        return json.dumps(
            {
                "time": self.time.timestamp() if isinstance(self.time, datetime.datetime) else self.time,
                "data": self.data,
                "id": self.id
            },
        )


class DataLogger:
    def __init__(self):
        # use multiprocessing Queue so that
        # classifier can run in separate process
        self.data_queue = Queue()

        # auto create with timestamp
        timestr = time.strftime("%Y%m%d%H%M")
        if not os.path.exists(Config.datadir):
            os.makedirs(Config.datadir)
        self.filename = os.path.join(Config.datadir, timestr + ".jsonl")
        logging.debug(f"data will be written to {self.filename}")

    def __del__(self):
        # flush the queue
        self._write()

    def log(self, message: Union[DataPoint, dict]):
        logging.debug("entered logging function")
        if isinstance(message, DataPoint):
            data = message
        elif isinstance(message, dict):
            data = DataPoint(**message)
        else:
            raise Exception("Message format not supported")

        self.data_queue.put(data)

    def _write(self):
        # TODO: should probably set a datadir in the config and use it here
        with open(self.filename, 'a+') as f:
            while not self.data_queue.empty():
                f.write(str(self.data_queue.get_nowait()))

    async def write(self):
        '''
        :return: None
        '''
        with concurrent.futures.ThreadPoolExecutor() as executor:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(executor, self._write)

import logging
import inspect

from django.dispatch import Signal
from uuid import uuid4
from os import path


_dispatcher = Signal()

def _caller_function_info():
    prev_frame = inspect.currentframe().f_back.f_back.f_code
    return path.basename(prev_frame.co_filename), prev_frame.co_name

class Publisher:
    def __init__(self, publisher_id=None):
        if publisher_id:
            self.publisher_id = str(publisher_id) + "-" + uuid4().hex
        else:
            self.publisher_id = str(uuid4().hex)

    def publish(self, message, log_msg=None, no_log=None, **kwargs):
        if not no_log:
            logging.debug("({}:{}) {} published {}".format(
                *_caller_function_info(), self.publisher_id, log_msg or message))
        _dispatcher.send(sender=self.publisher_id, message=message, **kwargs)

class Subscriber:
    def subscribe(self, handler, publisher_id, name_in_log=None):
        logging.debug("({}:{}) {} subscribed to {}".format(
            *_caller_function_info(), name_in_log or _caller_function_info()[0], publisher_id))
        _dispatcher.connect(handler, sender=publisher_id)


from django.dispatch import Signal
import logging
import inspect
from os import path

_dispatcher = Signal()

class Publisher:
    def __init__(self, publisher_id=None):
        if publisher_id:
            self.publisher_id = publisher_id
        else:
            self.publisher_id = str(uuid4().hex)

    def publish(self, message, log=False, log_msg=None, **kwargs):
        if log:
            prev_frame = inspect.currentframe().f_back.f_code
            logging.debug("({}:{}) {} published {}".format(
                path.basename(prev_frame.co_filename), prev_frame.co_name,
                self.publisher_id, log_msg or message))
        _dispatcher.send(sender=self.publisher_id, message=message, **kwargs)

class Subscriber:
    def subscribe(self, handler, publisher_id):
        _dispatcher.connect(handler, sender=publisher_id)


from collections import deque
from nicls.data_logger import get_logger, Counter
import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import logging
import time

from nicls.pubsub import dispatcher, CLASSIFIER, BIOSEMI


class Classifier:
    # Create counters

    def __init__(self, source_channel, bufferlen=None,
                 samplerate=None, datarate=None, classiffreq=None):
        logging.info("initializing classifier")
        # self.class_id = Counter()
        # self.submitted_id = Counter()
        
        # Subscribe to data source(s))
        logging.info(f"subscribing classifier to data on channel {source_channel}")
        dispatcher.connect(self.biosemi_receiver, sender=BIOSEMI)
        self.source_channel = source_channel
        self._enabled = True

        # convert seconds to data packets
        self.ring_buf = deque(
            maxlen=int(bufferlen * (1 / samplerate) * (1 / datarate))
        )

    def biosemi_receiver(self, message, **kwargs):
        # TODO: check this is data and not 'error' or some such
        self.ring_buf.append(message)
        logging.info("data added")
        logging.info("fitting data")
        # i = self.class_id.GrabAndIncrement()
        fit_task = asyncio.create_task(self.fit())

    def load(self, data):
        # the loading here should construct the full processing chain,
        # which will run as part of fit
        t = time.time()
        pows = np.fft.fft(data)
        time.sleep(3)
        result = np.random.randint(0, 2)
        print(f"classification took {time.time()-t} seconds")
        return result

    # Want to pass in to fit something that will help track
    # the original order, so that classifier results can be matched
    # with the epochs they're classifying
    async def fit(self):
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=5) as executor:
            # TODO: while not cancelled

            # TODO: give this data
            # something involving the ring buffer
            result = await loop.run_in_executor(
                executor, self.load, np.array(list(self.ring_buf))
            )
        # self.check_submitted(this_id)
        logging.debug(f"publishing classifier result {result}")
        dispatcher.send(sender=CLASSIFIER, message=result)
        # self.submitted_id.GrabAndIncrement()

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    # def check_submitted(self, this_id):
    #     if not this_id - self.submitted_id.GrabAndIncrement() == 1:
    #         raise ValueError("Trying to publish out of order")

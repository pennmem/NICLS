from collections import deque
from nicls.data_logger import get_logger, Counter
from nicls.pubsub import Publisher, Subscriber
import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import logging
import time


class Classifier(Publisher, Subscriber):
    # Create counters

    def __init__(self, biosemi_publisher_id, bufferlen=None,
                 samplerate=None, datarate=None, classiffreq=None):
        super().__init__("CLASSIFIER")
        logging.info("initializing classifier")
        # convert seconds to data packets
        # Joey: I think this might be wrong as Connor wrote it
        buffer_packets = int(bufferlen * (1 / samplerate) * (1 / datarate))
        self.ring_buf = deque(
            maxlen=buffer_packets
        )
        # classifreq is a frequency, i.e. classifications / second
        # datarate is number of samples per tcp data packet
        # samplerate is samples / second
        # need a conversion to packets per classification, something like:
        # packets / class = (packets/sample)*(samples/s)*(s/class)

        self.npackets = int((1 / datarate) * samplerate * (1 / classiffreq))

        # make counter to track how many packets have arrived
        self.packet_count = 0

        # Subscribe to data source(s))
        logging.info(f"subscribing classifier to data on channel {biosemi_publisher_id}")
        self.subscribe(self.biosemi_receiver, biosemi_publisher_id)
        self._enabled = True

    def biosemi_receiver(self, message, **kwargs):
        self.packet_count += 1
        # TODO: check this is data and not 'error' or some such
        self.ring_buf.append(message)
        logging.info("fitting data")
        # only fit if we have a full buffer, skip npackets to avoid
        # launching too many processes 
        if ((self.packet_count % self.npackets == 0) & (self.packet_count>=buffer_packets)):
          asyncio.create_task(self.fit())  # Task not awaited

    def load(self, data):
        # the loading here should construct the full processing chain,
        # which will run as part of fit
        t = time.time()
        pows = np.fft.fft(data)
        time.sleep(3)
        result = np.random.randint(0, 2)
        print(f"classification took {time.time()-t} seconds")
        return result

    # TODO: Want to pass in to fit something that will help track
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
        self.publish(result, log=True)


    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

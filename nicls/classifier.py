from nicls.messages import MessageClient, get_broker, Message
from collections import deque
from nicls.data_logger import get_logger, Counter
import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import logging
import time


class Classifier(MessageClient):
    def __init__(self, source_channel, bufferlen=None,
                 samplerate=None, datarate=None, classiffreq=None):
        logging.info("initializing classifier")
        super().__init__()
        logging.info(
            f"subscribing classifier to data on channel {source_channel}"
        )
        # Subscribe to data source, but don't log data packets
        get_broker().subscribe(source_channel, self, log=False)
        self.source_channel = source_channel
        self._enabled = True

        # convert seconds to data packets
        # Joey: I think this might be wrong as Connor wrote it
        buffer_packets = int(bufferlen * (1 / samplerate) * (1 / datarate))
        logging.debug("initializing data queue")
        self.queue = deque(
            maxlen=buffer_packets
        )
        # classifreq is a frequency, i.e. classifications / second
        # datarate is number of samples per tcp data packet
        # samplerate is samples / second
        # need a conversion to packets per classification, something like:
        # packets / class = (packets/sample)*(samples/s)*(s/class)

        self.npackets = int((1 / datarate) * samplerate * (1 / classifreq))

        # make counter to track how many packets have arrived
        self.packet_count = 0

    def receive(self, channel: str, message: Message):
        logging.debug(f"receiving data from channel {channel}")
        if (channel == self.source_channel) & (self._enabled):
        	self.packet_count += 1
            # TODO: check this is data and not 'error' or some such

            # for a fixed length queue, this implicitly includes a popleft
            self.queue.append(message.payload)
            logging.info("data added")
            logging.info("fitting data")
            # only fit if we have a full buffer, skip npackets to avoid
            # launching too many processes 
            if ((self.packet_count % self.npackets == 0)&(self.packet_count>=buffer_packets)):
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
            # something involving the queue
            result = await loop.run_in_executor(
                executor, self.load, np.array(list(self.queue))
            )
        logging.debug(
            f"publishing classifier result {result} to {self.id}"
        )
        get_broker().publish(self.id, Message(self.id, result))

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

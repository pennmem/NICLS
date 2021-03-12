from nicls.messages import MessageClient, get_broker, Message
from collections import deque
# from data_logger import get_logger
import asyncio
import concurrent
import numpy as np
import logging


class Classifier(MessageClient):
    def __init__(self, source_channel, bufferlen=None,
                 samplerate=None, datarate=None, classiffreq=None):
        logging.info("initializing classifier")
        super().__init__()
        logging.info(f"subscribing classifier to data source on channel {source_channel}")
        get_broker().subscribe(source_channel, self)
        self.source_channel = source_channel

        # TODO: mechanism to enable/disable

        # convert seconds to data packets
        logging.debug("initializing data queue")
        self.queue = deque(
            maxlen=int(bufferlen * (1 / samplerate) * (1 / datarate))
        )
        # does this really need maxlen? that argument

    def receive(self, channel: str, message: Message):
        logging.debug(f"receiving data from channel {channel}")
        if channel == self.source_channel:
            # TODO: check this is data and not 'error' or some such

            # for a fixed length queue, this implicitly includes a popleft
            self.queue.append(message.payload)
            logging.info("data added")

    def load(self):
        # the loading here should construct the full processing chain,
        # which will run as part of fit
        logging.debug("grabbing data from queue")
        chunk = self.popleft()
        result = np.random.randint(0, 2)
        logging.info(f"classifier result: {result}")
        return result

    async def fit(self):
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # TODO: while not cancelled

            # TODO: give this data
            # something involving the queue
            result = await asyncio.run_in_executor(
                executor, self.load, self.queue)
            get_broker().publish(self.id, Message(self.id, result))

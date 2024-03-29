import asyncio
import logging
import numpy as np

from nicls.pubsub import Publisher
from functools import partial

# samples / channel, width of bytes
SAMPLES = 16
WIDTH = 3

class BioSemiListener(Publisher):
    def __init__(self, host, port, channels):
        super().__init__("BIOSEMI")
        self.host = host
        self.port = port
        self.channels = channels

    async def connect(self):
        logging.debug("attempting to connect biosemi")
        self.reader, self.writer = await asyncio.open_connection(self.host,
                                                                 self.port)
        logging.debug("connected to biosemi")
        asyncio.create_task(self.listen())  # Task not awaited

    async def listen(self):
        ''' Read packets of data from the biosemi system and
        publish them to the channel for object id.

        :return: None
        '''

        while not self.reader.at_eof():
            # NOTE: this may need to handle incomplete packets
            try:
                data = await self.reader.readexactly(
                    self.channels * SAMPLES * WIDTH
                    )
            except asyncio.IncompleteReadError as e:
                # TODO
                logging.warning(e)
                print(e)
            self.publish(self.parse(data), log_msg="biosemi data", no_log=True)

    def parse(self, data: bytes):
        ''' Data format is 24 bytes per channel, repeated 8 times,
        so this function cuts this into a matrix with shape
        (channels, samples).

        :param data: little endian ordered data
        :return: np.array with shape (channels, samples)
        '''
        # changed comprehension from generator to list because it was exhausted
        # before being mapped. apparently poorly defined.
        data = map(partial(int.from_bytes, byteorder="little", signed=True),
                   [data[i:i + WIDTH] for i in range(0, len(data), WIDTH)])
        return np.array(list(data)).reshape(SAMPLES, self.channels)

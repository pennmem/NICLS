import asyncio
from nicls.messages import MessageClient, Message, get_broker
from functools import partial
import numpy as np
import logging
import concurrent

SAMPLES = 8
WIDTH = 3


class BioSemiListener(MessageClient):
    def __init__(self, host, port, channels):
        super().__init__()

        self.host = host
        self.port = port
        self.channels = channels

    def receive(self, channel: str, message: Message):
        raise NotImplementedError(
            "BioSemiListener blindly sends data until cancelled."
            "It does not intend to subscribe to any channels."
        )

    async def connect(self):
        logging.debug("attempting to connect biosemi")
        self.reader, self.writer = await asyncio.open_connection(self.host,
                                                                 self.port)
        logging.debug("connected to biosemi")
        task = asyncio.create_task(self.listen())

    async def listen(self):
        ''' Read packets of data from the biosemi system and
        publish them to the channel for object id.

        :return: None
        '''

        while not self.reader.at_eof():
            # NOTE: this may need to handle incomplete packets
            try:
                data = await self.reader.readexactly(
                    self.channels * SAMPLES * WIDTH)
            except asyncio.IncompleteReadError as e:
                # TODO
                logging.warning(e)
                print(e)

            get_broker().publish(self.id, Message(self.id, self.parse(data)))
            logging.debug(f"publishing data to channel {self.id}")

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
        return np.array(list(data)).reshape(self.channels, SAMPLES)

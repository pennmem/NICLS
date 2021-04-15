import asyncio
import multiprocessing
import logging
import time
import numpy as np

from collections import deque
from concurrent.futures import ProcessPoolExecutor
from nicls.data_logger import get_logger, Counter
from nicls.pubsub import Publisher, Subscriber

class Classifier(Publisher, Subscriber):
    _process_pool_executor = None
    _cores = 1

    # The process pool is static so if we use more than one classifier 
    # then all the objects will share the same process pool
    @staticmethod
    def setup_process_pool(cores=1):
        if Classifier._process_pool_executor == None:
            Classifier._process_pool_executor = ProcessPoolExecutor(max_workers=cores)
            Classifier._cores = cores
        else:
            raise RuntimeError(f"Process pool already set up with {Classifier._cores} workers")

    def __init__(self, biosemi_publisher_id, secs_of_data_buffered=None,
                 samplerate=None, datarate=None, classiffreq=None):
        super().__init__("CLASSIFIER")
        logging.info("initializing classifier")

        if Classifier._process_pool_executor == None:
            raise RuntimeError('Classifier process pool never set up. Please use "Classifier.setup_process_pool(...)"')

        self._enabled = True

        # convert seconds to data packets
        buffer_len = int(secs_of_data_buffered * (1/datarate) * samplerate)
        self.ring_buf = deque(maxlen=buffer_len)

        # classiffreq is a frequency, i.e. classifications / second
        # datarate is number of samples per tcp data packet
        # samplerate is samples / second
        # need a conversion to packets per classification:
        # packets / classification = (packets/sample)*(samples/s)*(s/classification)
        self.npackets = int((1 / datarate) * samplerate * (1 / classiffreq) * (1 / Classifier._cores))
        self.packet_count = 0  # track how many packets have arrived

        # Subscribe to data source(s))
        self.subscribe(self.biosemi_receiver, biosemi_publisher_id, name_in_log="Classifier")

    def biosemi_receiver(self, message, **kwargs):
        # TODO: check this is data and not 'error' or some such
        self.ring_buf.append(message)
        # Skip npackets to avoid launching too many processes 
        self.packet_count += 1
        if ((self.packet_count % self.npackets == 0) and self._enabled):
            # Only fit if we have a full buffer
            if self.packet_count < self.ring_buf.maxlen:
                logging.warning("Not enough biosemi data collected yet, please wait.")
            else:
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
        logging.info("fitting data")
        loop = asyncio.get_running_loop() #JPB: TODO: Catch exception?
        result = await loop.run_in_executor(
            Classifier._process_pool_executor, self.load, np.array(list(self.ring_buf))
        )
        self.publish(result, log=True)


    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

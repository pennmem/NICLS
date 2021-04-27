import asyncio
import multiprocessing
import logging
import time
import numpy as np
import json
from sklearn.linear_model import LogisticRegression
from ptsa.data.filters import ButterworthFilter, MorletWaveletFilter
from ptsa.data.timeseries import TimeSeries

from collections import deque
from concurrent.futures import ProcessPoolExecutor
from nicls.data_logger import get_logger, Counter
from nicls.pubsub import Publisher, Subscriber
from nicls.configuration import Config


class Classifier(Publisher, Subscriber):
    _process_pool_executor = None
    _cores = 1

    # The process pool is static so if we use more than one classifier
    # then all the objects will share the same process pool
    @staticmethod
    def setup_process_pool(cores=1):
        if Classifier._process_pool_executor is None:
            Classifier._process_pool_executor = ProcessPoolExecutor(
                max_workers=cores)
            Classifier._cores = cores
        else:
            raise RuntimeError("Process pool already set up with "
                               f"{Classifier._cores} workers")

    def __init__(self, biosemi_publisher_id, secs_of_data_buffered=None,
                 samplerate=None, datarate=None, classiffreq=None):
        super().__init__("CLASSIFIER")
        logging.info("initializing classifier")
        self.samplerate = samplerate

        if Classifier._process_pool_executor is None:
            raise RuntimeError(
                'Classifier process pool never set up. '
                'Please use "Classifier.setup_process_pool(...)"')

        self._enabled = True

        # load classifier from json
        self.model = ClassifierModel(
            LogisticRegression()
        ).load_json(Config.classifier.filepath).get()

        # convert seconds to data packets
        buffer_len = int(secs_of_data_buffered * (1 / datarate) * samplerate)
        self.ring_buf = deque(maxlen=buffer_len)

        # classiffreq is a frequency, i.e. classifications / second
        # datarate is number of samples per tcp data packet
        # samplerate is samples / second
        # need a conversion to packets per classification:
        # packets / classification =
        #       (packets/sample)*(samples/s)*(s/classification)
        self.npackets = int((1 / datarate) * samplerate *
                            (1 / classiffreq) * (1 / Classifier._cores))
        self.packet_count = 0  # track how many packets have arrived

        # Subscribe to data source(s))
        self.subscribe(self.biosemi_receiver,
                       biosemi_publisher_id, name_in_log="Classifier")

    def biosemi_receiver(self, message, **kwargs):
        # TODO: check this is data and not 'error' or some such
        self.ring_buf.append(message)
        # Skip npackets to avoid launching too many processes
        self.packet_count += 1
        if ((self.packet_count % self.npackets == 0) and self._enabled):
            # Only fit if we have a full buffer
            if self.packet_count < self.ring_buf.maxlen:
                logging.warning(
                    "Not enough biosemi data collected yet, please wait.")
            else:
                asyncio.create_task(self.fit())  # Task not awaited

    def load(self, data, config):
        # the loading here should construct the full processing chain,
        # which will run as part of fit
        t = time.time()
        # stack data along first axis (samples)
        # then, transpose to make array channels x samples
        data = np.vstack(data).T
        eeg = TimeSeries(data,
                         coords={'samplerate': self.samplerate},
                         dims=['channel', 'time']
                         )
        # filter out line noise
        eeg = ButterworthFilter(eeg, filt_type='stop', freq_range=[
                                58, 62], order=4).filter()
        # highpass filter 0.5 Hz to ignore drift
        eeg = ButterworthFilter(eeg, filt_type='highpass',
                                freq_range=0.5).filter()
        # Wavelet power decomposition
        # FIXME: what's the right number of cpus?
        # FIXME: do freqs programatically
        buffer_time = 0
        freq_specs = config['freq_specs']
        freqs = np.logspace(np.log10(freq_specs[0]),
                            np.log10(freq_specs[1]),
                            freq_specs[2])
        pows = MorletWaveletFilter(eeg,
                                   freqs=freqs,
                                   width=4,
                                   output='power',
                                   cpus=5).filter()
        pows.remove_buffer(buffer_time)
        pows = pows.data + np.finfo(np.float).eps / 2.
        # log transform
        log_pows = np.log10(pows)
        # average over time/samples
        avg_pows = np.nanmean(log_pows, -1)
        # reshape as events x features (only one event epoch)
        avg_pows = avg_pows.reshape((1, -1))
        result = self.model.predict(avg_pows)
        print(f"classification took {time.time()-t} seconds")
        return result[0]

    # TODO: Want to pass in to fit something that will help track
    # the original order, so that classifier results can be matched
    # with the epochs they're classifying
    async def fit(self):
        logging.info("fitting data")
        loop = asyncio.get_running_loop()  # JPB: TODO: Catch exception?
        classifier_config = Config.classifier.get_dict()
        result = await loop.run_in_executor(
            Classifier._process_pool_executor, self.load, np.array(
                list(self.ring_buf)), classifier_config
        )
        self.publish(result, log=True)

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

# Lightweight wrapper class for saving and loading sklearn models
# as json


class ClassifierModel:
    def __init__(self, model):
        self.model = model
        self.model_params = model.__dict__

    def save_json(self, filepath):
        for k, v in self.model_params.items():
            if isinstance(v, np.ndarray):
                self.model_params[k] = v.tolist()
        json_text = json.dumps(self.model_params)
        with open(filepath, 'w') as file:
            file.write(json_text)

    def load_json(self, filepath):
        with open(filepath, 'r') as file:
            self.model_params = json.load(file)
        for k, v in self.model_params.items():
            if isinstance(v, list):
                self.model_params[k] = np.asarray(v)
        self.model.__dict__ = self.model_params
        return self

    def get(self):
        return self.model

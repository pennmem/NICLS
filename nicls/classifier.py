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
        self.secs_of_data_buffered = secs_of_data_buffered

        if Classifier._process_pool_executor is None:
            raise RuntimeError(
                'Classifier process pool never set up. '
                'Please use "Classifier.setup_process_pool(...)"')

        self._enabled = True
        self._encoding = False
        self._encoding_stats = None
        # features vector is shape (1, freqs x channels)
        self.num_feats = Config.classifier.freq_specs[2] * \
            Config.biosemi.channels
        self._online_statistics = OnlineStatistics(self.num_feats)

        # load classifier from json
        self.model = ClassifierModel(
            LogisticRegression()
        ).load_json(Config.classifier.filepath).get()

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

        # Only run stats or fit if we have a full buffer
        if len(self.ring_buf) < self.ring_buf.maxlen:
            logging.warning(
                "Not enough biosemi data collected yet, please wait.")
        else:
            if self._encoding:
                # only process one epoch per word presentation
                self._encoding = False
                asyncio.create_task(self.encoding_stats())

            # Skip npackets to avoid launching too many processes
            self.packet_count += 1
            if ((self.packet_count % self.npackets == 0) and self._enabled):
                self.publish({"EEG_EPOCH_END":{"id":0, "duration":-1, "wavelet_buffs":-2}}result, log=True)
                asyncio.create_task(self.fit())  # Task not awaited

    def powers(self, data, config: dict, norm: tuple = (0, 1)):
        """
        Process an incoming eeg buffer and compute PSD
        Parameters:
        data - eeg buffer
        config - dict with parameters for wavelet analysis
        norm - tuple of array-like with (mean, std) for normalizing
            each feature
        Returns:
        norm_pows - normalized powers with shape 1 x n_feats
        """
        # the loading here should construct the full processing chain,
        # which will run as part of fit
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
        freq_specs = config['freq_specs']
        freqs = np.logspace(np.log10(freq_specs[0]),
                            np.log10(freq_specs[1]),
                            freq_specs[2])
        # width is really n_cycles, buffer needs to be at least half
        # the width at the lowest frequency
        buffer_time = 1 / freq_specs[0] * config['wavelet_width'] / 2
        pows = MorletWaveletFilter(eeg,
                                   freqs=freqs,
                                   width=config['wavelet_width'],
                                   output='power',
                                   cpus=5).filter()
        pows = pows.remove_buffer(buffer_time).data + \
            np.finfo(np.float).eps / 2.
        # log transform
        log_pows = np.log10(pows)
        # average over time/samples
        avg_pows = np.nanmean(log_pows, -1)
        # reshape as events x features (only one event epoch)
        avg_pows = avg_pows.reshape((1, -1))
        # normalize powers
        norm_pows = (avg_pows - norm[0]) / norm[1]
        return norm_pows

    async def encoding_stats(self):
        t = time.time()
        logging.info("calculating encoding stats")

        loop = asyncio.get_running_loop()  # JPB: TODO: Catch exception?
        # pass in configuration parameters for analysis
        classifier_config = Config.classifier.get_dict()
        # TODO: pass in normalization params
        powers = await loop.run_in_executor(
            Classifier._process_pool_executor, self.powers, np.array(
                list(self.ring_buf)), classifier_config
        )
        # .update() expects a column vectors of feature powers
        logging.info("Updating online stats")
        self._online_statistics.update(powers)

        print(f"encoding stats took {time.time()-t} seconds")

    # TODO: Want to pass in to fit something that will help track
    # the original order, so that classifier results can be matched
    # with the epochs they're classifying
    async def fit(self):
        t = time.time()
        logging.info("fitting data")

        if not self._encoding_stats:
            logging.warning("Classifier fitting without normalization")
            stats = (0, 1)
        else:
	    # Use sample std, not population std (ddof = 1)
            stats = (self._encoding_stats[0], self._encoding_stats[2])

        loop = asyncio.get_running_loop()  # JPB: TODO: Catch exception?
        # pass in configuration parameters for analysis
        classifier_config = Config.classifier.get_dict()
        powers = await loop.run_in_executor(
            Classifier._process_pool_executor, self.powers, np.array(
                list(self.ring_buf)), classifier_config, stats
        )
        # why predict(powers)[0]? Just to have the right data type, it's size 1 anyway
        prob = self.model.predict_proba(powers)[0, 1]
        result = prob > 0.5 
        print(f"classification took {time.time()-t} seconds")
        self.publish({"CLASSIFIER_RESULT":{"id":0, "result":result, "probability":prob}}result, log=True)

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def encoding(self, enabled):
        print('--------------------')
        print('ENCODING: ' + str(enabled))
        print('--------------------')
        self._encoding = enabled

    def read_only_state(self, enabled):
        print('--------------------')
        print('READ_ONLY_STATE: ' + str(enabled))
        print('--------------------')
        if enabled:
            self._online_statistics.reset()
            self._encoding_stats = None
        else:
            self._encoding_stats = self._online_statistics.finalize()
            logging.info("_encoding_stats have been finalized")
            logging.info(f"mean:{self._encoding_stats[0]}, std: {self._encoding_stats[1]}")

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


class OnlineStatistics:
    def __init__(self, num_feats):
        self._existingAggregate = (0,
                                   np.zeros((1, num_feats)),
                                   np.zeros((1, num_feats)))

    def reset(self):
        (count, mean, M2) = self._existingAggregate
        self._existingAggregate = (0,
                                   np.zeros((1, mean.size)),
                                   np.zeros((1, M2.size)))

    # For a new features vector newFeats, compute the new count, new mean, the new M2.
    # mean accumulates the mean of the entire dataset
    # M2 aggregates the squared distance from the mean
    # count aggregates the number of samples seen so far
    def update(self, newFeats):
        (count, mean, M2) = self._existingAggregate
        count += 1
        delta = newFeats - mean
        mean += delta / count
        delta2 = newFeats - mean
        M2 += delta * delta2
        self._existingAggregate = (count, mean, M2)

    # Retrieve the mean, std dev and sample std dev from an aggregate
    def finalize(self):
        (count, mean, M2) = self._existingAggregate
        if count < 2:
            print(count)  
            raise RuntimeError("Variable count is less than 2")
        else:
            (mean, variance, sampleVariance) = (
                mean, M2 / count, M2 / (count - 1))
            return (mean, np.sqrt(variance), np.sqrt(sampleVariance))

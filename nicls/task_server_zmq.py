import json
import asyncio
import datetime
import logging

from collections import deque
from nicls.data_logger import DataPoint, get_logger
from nicls.configuration import Config
from nicls.biosemi_listener import BioSemiListener
from nicls.classifier import Classifier
from nicls.pubsub import Subscriber 

import zmq
import zmq.asyncio

class TaskMessage(DataPoint):
    # FIXME: protect internal args
    def __init__(self, ev_type, time=None, sent=False, **kwargs):
        super().__init__(time=time, **kwargs)
        self.type = ev_type
        self.sent = sent

    @staticmethod
    def from_bytes(message):
        raw_data = json.loads(message.decode('utf-8'))

        try:
            #msgid = raw_data.pop("id")
            msgid = -1
            msg = TaskMessage(raw_data.pop("type"), time=raw_data.pop(
                "time"), sent=True, **raw_data.pop("data"))
        except KeyError:
            raise KeyError("Not a valid TaskMessage")

        msg.id = msgid
        return msg

    def __str__(self):
        return json.dumps(
            # FIXME log sent, but don't send over network
            {
                "type": self.type,
                "data": self.data,
                "time": self.time.timestamp() if
                isinstance(self.time, datetime.datetime) else self.time,
                # JPB: TODO: MVP2: add id
                #"id": self.id
            }, 
            separators=(',', ':')
        )
        # JPB: TODO: add new line to make this json lines 

    def __bytes__(self):
        return str(self).encode("utf-8")

class TaskServer(Subscriber):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._sock = None 

    async def __aenter__(self):
        self._sock = zmq.asyncio.Context().socket(zmq.PAIR)
        #self._sock.bind(f'tcp://{self._host}:{self._port}')
        self._sock.bind(f'tcp://*:{self._port}')
        return self.listen()

    async def __aexit__(self):
        self._close()

    async def _send(self, msg):
        if self._sock:
            await self._sock.send(msg.encode('UTF-8'))

    async def _recv(self):
        if self._sock:
            return await self._sock.recv() 

    async def _close(self, msg=None):
        if self._sock:
            if msg:
                await self._sock.send(msg)
            self._sock.close()
        self._sock = None

    def _check_configuration(self, received_config):
        # TODO
        logging.info("checking configuration")
        return True

    async def _run_configuration(self):
        # Setup Biosemi
        self.biosemi_source = BioSemiListener(Config.biosemi.host,
                                           Config.biosemi.port,
                                           Config.biosemi.channels)

        # Setup Classifier
        # Connor: TODO: if we use different classifier versions or the like,
        # we'll need subclasses or a factory
        Classifier.setup_process_pool(Config.system.cores)
        self.classifier = Classifier(self.biosemi_source.publisher_id,
                                     Config.classifier.secsdatabuffered,
                                     Config.classifier.samplerate,
                                     Config.classifier.datarate,
                                     Config.classifier.classiffreq)
        self.subscribe(self._classifier_receiver, self.classifier.publisher_id, name_in_log="TaskConnection")

        # Connect to all of the sources
        await self.biosemi_source.connect()
        logging.info("task server connected to biosemi listener")

    def _classifier_receiver(self, message, **kwargs):
        logging.info(f"task server received classifier result: {message}")
        out_message = TaskMessage("classifier", **{"label": message})
        # JPB: TODO: MVP2: Make classifier send TaskMessage
        #asyncio.create_task(self._send(str(out_message)))  # Task not awaited
        asyncio.create_task(self._send(str(message)))

    async def listen(self):
        while self._sock:
            message = await self._recv()
            # JPB: TODO: MVP2: Remove this and make everything work with TaskMessages
            # TEMP START ----------------------------------
            print(message)
            if message == b'CONNECTED':
                await self._send("CONNECTED")
            elif message == b'CONFIGURE':
                if self._check_configuration(""):
                    try:
                        await self._run_configuration()
                        await self._send('CONFIGURE')
                    except RuntimeError as e:
                        await self._close('ERROR_IN_CONFIGURATION')
                        raise e
                else:
                    await self._close('ERROR_IN_CONFIG_FILE')
            else:
            # TEMP END -------------------------------------
                message = TaskMessage.from_bytes(message)
                if message.type == 'ENCODING':
                    print("---------------")
                    print("ENCODING STUFF")
                    self.classifier.encoding(message.data['enable'])
                    print("---------------")
                get_logger().log(message)
                print(message)
            continue

            # JPB: TODO: Convert these to enums
            if message.type == 'CONNECTED':
                await self._send(TaskMessage('CONNECTED'))
            elif message.type == 'HEARTBEAT':
                await self._send(TaskMessage('HEARTBEAT'))
            elif message.type == 'CONFIGURE':
                if self._check_configuration(message.data):
                    try:
                        await self._run_configuration()
                        await self._send(TaskMessage('CONFIGURE'))
                    except RuntimeError as e:
                        await self._close(TaskMessage('ERROR_IN_CONFIGURATION'))
                        raise e
                else:
                    await self._close(TaskMessage('ERROR_IN_CONFIG_FILE'))
            elif message.type == "CLASSIFIER_ON":
                self.classifier.enable()
            elif message.type == "CLASSIFIER_OFF":
                self.classifier.disable()




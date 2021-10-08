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


class TaskMessage(DataPoint):
    # FIXME: protect internal args
    def __init__(self, ev_type, time=None, sent=False, **kwargs):
        super().__init__(time=time, **kwargs)
        self.type = ev_type
        self.sent = sent

    @staticmethod
    def from_bytes(message):
        raw_data = json.loads(message.decode('utf-8', errors='ignore'))

        try:
            msg = TaskMessage(raw_data.pop("type"), time=raw_data.pop(
                "time"), sent=True, **raw_data.pop("data"))
        except KeyError:
            raise KeyError("Not a valid TaskMessage")

        return msg

    def __str__(self):
        return json.dumps(
            # FIXME log sent, but don't send over network
            {
                "type": self.type,
                "time": self.time.timestamp() if
                isinstance(self.time, datetime.datetime) else self.time,
                "data": self.data,
            }
        ) + "\n"

    def __bytes__(self):
        return str(self).encode("utf-8")


class TaskServer:
    def __init__(self, host, port):
        ''' This creates a persistent server that accepts connections
        from tasks and passes communication off to TaskConnection
        instances for setup of task requirements an communication
        with task.

        :param host:
        :param port:
        '''
        super().__init__()

        self.buffer = deque()

        self.host = host
        self.port = port

        self.server = None

    async def __aenter__(self):
        if self.server is not None:
            # TODO: warn
            return self.server.serve_forever()

        logging.info("starting task server")
        self.server = await asyncio.start_server(TaskServer._accept_connection,
                                                 self.host,
                                                 self.port)
        return self.server.serve_forever()

    async def __aexit__(self, exc_type, exc, tb):
        logging.info("closing server")
        self.server.close()
        await self.server.wait_closed()
        self.server = None
        logging.info("server closed successfully")

    @staticmethod
    async def _accept_connection(reader, writer):
        logging.debug("accepting connection")
        logging.debug("reader: " + str(reader))
        logging.debug("writer: " + str(writer))
        await TaskConnection(reader, writer).listen()


class TaskConnection(Subscriber):
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    def classifier_receiver(self, message, **kwargs):
        logging.info(f"task server received classifier result: {message}")
        message_name = list(message.keys())[0]
        out_message = TaskMessage(message_name, message[message_name])
        asyncio.create_task(self.send(out_message))  # Task not awaited

    async def listen(self):
        while not self.reader.at_eof():
            try:
                message = await self.reader.readline()
            except asyncio.LimitOverrunError as e:
                # TODO
                print(e)
            except asyncio.IncompleteReadError as e:
                # TODO
                print(e)

            print(message)
            message = TaskMessage.from_bytes(message)
            get_logger().log(message)

            # JPB: TODO: Convert these to enums
            if message.type == 'CONNECTED':
                await self.send(TaskMessage('CONNECTED_OK'))
            elif message.type == 'HEARTBEAT':
                await self.send(TaskMessage('HEARTBEAT_OK'))
            elif message.type == 'CONFIGURE':
                if self._check_configuration(message.data):
                    try:
                        await self._run_configuration()
                        await self.send(TaskMessage('CONFIGURE_OK', Config.get_dict()))
                    except RuntimeError as e:
                        await self.close(TaskMessage('ERROR_IN_CONFIGURATION'))
                        raise e
                else:
                    await self.close(TaskMessage('ERROR_IN_CONFIG_FILE'))
            elif message.type == "CLASSIFIER_ON":
                self.classifier.enable()
            elif message.type == "CLASSIFIER_OFF":
                self.classifier.disable()
            if message.type == 'ENCODING':
                self.classifier.encoding(message.data['enable'])
            elif message.type == 'READ_ONLY_STATE':
                self.classifier.read_only_state(message.data['enable'])

    async def send(self, message: TaskMessage):
        self.writer.write(bytes(message))
        get_logger().log(message)
        # JPB: This has a bug that drain doesn't actually wait till evrything is sent
        # This problem is particularly bad when the program finishes when the drain is low enough but the buffer isn't empty
        # Check Bug #3 on this webpage: https://vorpus.org/blog/some-thoughts-on-asynchronous-api-design-in-a-post-asyncawait-world/#example-3-asyncio-with-async-await
        await self.writer.drain()

    async def close(self, message: TaskMessage = None):
        if message:
            await self.send(message)
        self.writer.close()
        await self.writer.wait_closed()

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
        self.subscribe(self.classifier_receiver, self.classifier.publisher_id, name_in_log="TaskConnection")

        # Connect to all of the sources
        await self.biosemi_source.connect()
        logging.info("task server connected to biosemi listener")


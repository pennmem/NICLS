import asyncio
import datetime
import json
from collections import deque
from nicls.data_logger import DataPoint
from nicls.messages import MessageClient, Message, get_broker
from nicls.data_logger import get_logger


class TaskMessage(DataPoint):
    # FIXME: protect internal args
    def __init__(self, ev_type, time=None, sent=False, **kwargs):
        super().__init__(time=time, **kwargs)
        self.type = ev_type
        self.sent=sent

    @staticmethod
    def from_bytes(message):
        raw_data = json.loads(message.decode('utf-8'))

        try:
            msgid = raw_data.pop("id")
            msg = TaskMessage(raw_data.pop("type"), time=raw_data.pop("time"), sent=True, **raw_data)
        except KeyError as e:
            raise KeyError("Not a valid TaskMessage")

        msg.id = msgid
        return msg

    def __str__(self):
        return json.dumps(
            # FIXME log sent, but don't send over network
            {
                "type": self.type,
                "time": self.time.timestamp() if isinstance(self.time, datetime.datetime) else self.time,
                "data": self.data,
                "id":   self.id
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

        self.server = await asyncio.start_server(TaskServer._accept_connection, self.host, self.port)
        return self.server.serve_forever()

    async def __aexit__(self, exc_type, exc, tb):
        self.server.close()
        await self.server.wait_closed()
        self.server = None

    @staticmethod
    async def _accept_connection(reader, writer):
        await TaskConnection(reader, writer).listen()


class TaskConnection(MessageClient):
    def __init__(self, reader, writer):
        super().__init__()

        self.reader = reader
        self.writer = writer

    def receive(self, channel: str, message: Message):
        # TODO
        pass

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

            message = TaskMessage.from_bytes(message)
            get_logger().log(message)

            if message.type == 'CONNECTED':
                await self.send(bytes(TaskMessage('CONNECTED_OK')))

            elif message.type == 'CONFIGURE':
                if self._check_configuration(message.data):

                    # TODO: set up classifier, connect to biosemi
                    # if we use different classifier versions or the like,
                    # we'll need subclasses or a factory
                    # self.data_source = BioSemiListener(Config.biosemi.host,
                    #                                    Config.biosemi.port,
                    #                                    Config.biosemi.channels)
                    # self.classifier = Classifier(self.data_source.id, Config.classifier)
                    # get_broker().subscribe(self.classifier.id)
                    await self.send(bytes(TaskMessage('CONFIGURE_OK')))
                else:
                    # TODO: close connection
                    await self.send(bytes(TaskMessage('ERROR')))

            elif message.type == 'HEARTBEAT':
                await self.send(bytes(TaskMessage('HEARTBEAT_OK')))

    async def send(self, message: TaskMessage):
        self.writer.write(message)
        await self.writer.drain()

    def _check_configuration(self, received_config):
        # TODO
        return True
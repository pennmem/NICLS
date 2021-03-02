from collections import namedtuple
from uuid import uuid4

'''
Very, very basic MQTT like messaging system. A more sophisticated version
would implement caching for messages, notify clients, and allow clients
to grab messages when they are ready to handle them
'''

Message = namedtuple("Message", ["origin", "payload"])

_broker = None


def get_broker():
    global _broker

    if _broker is None:
        _broker = MessageBroker()

    return _broker


class MessageClient:
    def __init__(self):
        self.id = str(uuid4().hex)

    # TODO: we get to async this to await messages to a channel
    # TODO: make receive add messages to message queue
    def receive(self, channel: str, message: Message):
        ''' Looking forward to Python 3.10, this can use matching
        to match callback to channel/message type

        :param channel: the name of the channel from which the message is sent
        :param message: the message payload
        :return: None
        '''
        raise NotImplementedError("This is an interface function."
                                  "Clients should override this to "
                                  "handle messages.")


class MessageChannel:
    # TODO: allow additional metadata on channels
    def __init__(self, name: str, log=True):
        self.name = name
        self.subscribers = set()
        self.log = log

    def publish(self, message: Message):
        if self.log:
            # TODO: log messages that pass through channel
            pass

        for client in self.subscribers:
            client.receive(self.name, message)

    def subscribe(self, client: MessageClient):
        if client not in self.subscribers:
            self.subscribers.add(client)

    def unsubscribe(self, client: MessageClient):
        if client in self.subscribers:
            self.subscribers.remove(client)


class MessageBroker:
    '''
    Design note: in general, clients decide who to listen to, rather than who to send to. Objects
    expecting direct communication, such as the logger, have an explicit mechanism for doing so.
    '''

    def __init__(self):
        self.channels = {}

    def subscribe(self, channel: str, client: MessageClient):
        if channel in self.channels:
            self.channels[channel].subscribe(client)

    def unsubscribe(self, channel: str, client: MessageClient):
        if channel not in self.channels:
            self.channels[channel] = MessageChannel(channel)
        self.channels[channel].unsubscribe(client)

    def publish(self, channel, message: Message):
        if channel not in self.channels:
            self.channels[channel] = MessageChannel(channel)
        self.channels[channel].publish(message)

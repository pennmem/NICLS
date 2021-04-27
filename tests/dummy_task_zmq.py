from nicls.task_server import TaskMessage
from nicls.utils import repeated_invoke
import logging

import asyncio
import zmq
import zmq.asyncio



class DummyTask:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.is_beating = False

    async def connect(self):
        logging.info("connecting task")
        self._sock = zmq.asyncio.Context().socket(zmq.PAIR)
        self._sock.connect(f'tcp://{self.host}:{self.port}')
        
        # CONNECT
        await self._sock.send("CONNECTED".encode('UTF-8'))
        
        message = await self._sock.recv()
        if message.decode('UTF-8') != "CONNECTED":
            raise Exception("Task server not connected")
        logging.debug("task server connected")

        # CONFIGURE
        await self._sock.send("CONFIGURE".encode('UTF-8'))
        message = await self._sock.recv()
        if message.decode('UTF-8') != "CONFIGURE":
            raise Exception("Task server not configured")
        logging.debug("task server configured")
        # LATENCY CHECK
        # logging.debug("starting latency check")
        # for i in range(20):
        #     try:
        #         await asyncio.wait_for(self._heartbeat(), .2)
        #     except:
        #         raise Exception("Latency check failed")

        #     # the actual task waits for 200ms - time elapsed;
        #     # this is an irrelevant detail for the moment, but
        #     # could be implemented here for completeness
        #     await asyncio.sleep(.2)

        #await asyncio.gather(
        #    self.listen(), repeated_invoke(self._heartbeat, 1)
        #)

        await asyncio.gather(self.listen2())

    async def listen2(self):
        while True:
            classifier_result = await self._sock.recv()
            logging.debug('-----------------------------------------------')
            logging.debug("classifier result: " + classifier_result.decode('UTF-8'))
            logging.debug('-----------------------------------------------')

    async def _heartbeat(self):
        logging.debug("send Heartbeat")
        await self._sock.send("HEARTBEAT".encode('UTF-8'))
        # await self.wait_for("HEARTBEAT")
        # message = await self.reader.readline()

        # FIXME: pass through other messages until timeout
        # if TaskMessage.from_bytes(message).type != 'HEARTBEAT_OK':
        #     raise Exception("Missed Heartbeat")

        # reading in both _heartbeat and listen causes collision
        # instead have listen change boolean monitor
        await asyncio.sleep(.2)
        if not self.is_beating:
            raise Exception("Missed Heartbeat")

    async def listen(self):
        while not self.reader.at_eof():
            lock = asyncio.Lock()
            async with lock:
                message = await self.reader.readline()
            if TaskMessage.from_bytes(message).type == 'HEARTBEAT_OK':
                logging.debug("heartbeat returned")
                self.is_beating = True

            message = message.decode('utf-8')
            # print(message)


async def main():
    logging.debug("dummy task running")
    await DummyTask().connect()

if __name__ == "__main__":
    asyncio.run(main())

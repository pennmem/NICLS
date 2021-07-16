import asyncio
from nicls.task_server import TaskMessage
from nicls.utils import repeated_invoke
import logging


class DummyTask:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.is_beating = False

    async def connect(self):
        logging.info("connecting task")
        self.reader, self.writer = await asyncio.open_connection(
            self.host,
            self.port
        )

        self.writer.write(bytes(TaskMessage("CONNECTED")))
        await self.writer.drain()

        message = await self.reader.readline()
        if TaskMessage.from_bytes(message).type != 'CONNECTED_OK':
            raise Exception("Task server not connected")

        # CONFIGURE
        self.writer.write(bytes(TaskMessage("CONFIGURE")))
        await self.writer.drain()

        message = await self.reader.readline()
        if TaskMessage.from_bytes(message).type != 'CONFIGURE_OK':
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

        print("Waiting for data to collect")
        await asyncio.sleep(15)
        print("Read Only State - ON")
        self.writer.write(bytes(TaskMessage("READ_ONLY_STATE", **{"enable": 1})))
        print("Encoding 1")
        self.writer.write(bytes(TaskMessage("ENCODING", **{"enable": 1})))
        await asyncio.sleep(4)
        print("Encoding 2")
        self.writer.write(bytes(TaskMessage("ENCODING", **{"enable": 1})))
        await asyncio.sleep(4)
        print("Read Only State - OFF")
        self.writer.write(bytes(TaskMessage("READ_ONLY_STATE", **{"enable": 0})))

        #await asyncio.gather(
        #    self.listen(), repeated_invoke(self._heartbeat, 1)
        #)

    async def _heartbeat(self):
        logging.debug("send Heartbeat")
        self.writer.write(bytes(TaskMessage("HEARTBEAT")))
        self.is_beating = False
        await self.writer.drain()
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

import asyncio
from nicls.task_server import TaskMessage
from nicls.utils import repeated_invoke
import logging


class DummyTask:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def connect(self):
        logging.info("connecting task")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

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
        logging.debug("starting latency check")
        for i in range(20):
            try:
                await asyncio.wait_for(self._heartbeat(), 3)  # .2
            except:
                raise Exception("Latency check failed")

            # the actual task waits for 200ms - time elapsed;
            # this is an irrelevant detail for the moment, but
            # could be implemented here for completeness
            await asyncio.sleep(.2)

        # asyncio.create_task(hb async for hb in )
        # await asyncio.gather(self.listen(), self._heartbeat())
        await asyncio.gather(
            self.listen(), repeated_invoke(self._heartbeat, 1)
        )

    async def _heartbeat(self):
        logging.debug("send Heartbeat")
        self.writer.write(bytes(TaskMessage("HEARTBEAT")))
        await self.writer.drain()

        # await self.wait_for("HEARTBEAT")
        message = await self.reader.readline()

        # FIXME: pass through other messages until timeout
        if TaskMessage.from_bytes(message).type != 'HEARTBEAT_OK':
            raise Exception("Missed Heartbeat")
        logging.debug("heartbeat returned")

    async def listen(self):
        while not self.reader.at_eof():
            message = await self.reader.readline()
            message = message.decode('utf-8')
            print(message)


async def main():
    logging.debug("dummy task running")
    await DummyTask().connect()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import numpy as np
from eegsim import EEGGen
from functools import partial


class DummyBiosemi:
    ''' Naively accept connections and send data with as 8 sample packets,
    with eight chunks of one little endian 24 bit sample per channel
    '''

    def __init__(self, host, port, channels):
        self.channels = channels
        self.host = host
        self.port = port

    async def __aenter__(self):
       self.server = await asyncio.start_server(self.send_bytes, self.host, self.port)
       return self.server.serve_forever()

    async def __aexit__(self, exc_type, exc, tb):
        self.server.close()
        await self.server.wait_closed()

    async def send_bytes(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        while not writer.is_closing():
            # use max and min two's complement signed 24 bit ints, with high as exclusive upper bound
            # data = np.random.randint(low=int(0x7fffff), high=int(0x7fffff) + 1, size=self.channels*8).tobytes()
            
            # send one integer value
            # data = b"\xff\xff\x7f" * self.channels * 8
            # writer.write(data)
                        
            gen = EEGGen(sampling_rate=1000)
            gen.EnablePinkNoise(50, 1)
            eeg = gen.Generate(.016)
            eeg = (eeg.reshape((len(eeg), 1)) + np.ones(self.channels)).ravel() 
            data = map(partial(int.to_bytes, length=3, byteorder="little", signed=True),
                   [int(eeg[i]) for i in range(0, len(eeg), 1)])
            bytes_str = b"".join(list(data))
            writer.write(bytes_str)

            await asyncio.sleep(0.008)


async def main():
    async with DummyBiosemi(128) as biosemi:
        await biosemi

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

import asyncio
from nicls.main import main as nicls
from dummy_biosemi import DummyBiosemi
from dummy_task import DummyTask
from pathlib import Path
from nicls.configuration import load_configuration, Config


async def main():
    # start the NICLS system
    load_configuration(Path("./config.json").absolute())
    nicls_server = asyncio.create_task(nicls())

    # start biosemi sending data and the task requesting it. These are
    # test systems that imitate the real behavior of the ActiView software
    # and UnityEPL tasks
    async with DummyBiosemi(Config.biosemi.host, \
                            Config.biosemi.port, \
                            Config.biosemi.channels) as biosemi:

        task = asyncio.create_task(DummyTask(Config.task.host, Config.task.port).connect())
        await asyncio.gather(task, biosemi, nicls_server)

if __name__ == "__main__":
    asyncio.run(main())

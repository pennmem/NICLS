import asyncio
from nicls.main import main as nicls
from dummy_biosemi import DummyBiosemi
from dummy_task import DummyTask
from pathlib import Path
from nicls.configuration import load_configuration, Config

# test for fake task + real biosemi

async def main():
    # start the NICLS system
    load_configuration(Path("./config.json").absolute())
    nicls_server = asyncio.create_task(nicls())

    task = asyncio.create_task(DummyTask(Config.task.host, Config.task.port).connect())
    await asyncio.gather(task, nicls_server)

if __name__ == "__main__":
    asyncio.run(main(), debug=True)

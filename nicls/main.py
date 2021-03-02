import asyncio
from nicls.task_server import TaskServer
from nicls.configuration import load_configuration, Config
from nicls.data_logger import get_logger
from nicls.utils import repeated_invoke


async def main():
    # set up logger
    logger = get_logger()
    logger_write = repeated_invoke(logger.write, 5)

    async with TaskServer(Config.task.host, Config.task.port) as task_server:
        await asyncio.gather(task_server, logger_write)

if __name__ == "__main__":
    # load config
    load_configuration("test/config.json")
    asyncio.run(main("tests/config.json"))

import asyncio
import logging

from nicls.configuration import load_configuration, Config
from nicls.data_logger import get_logger, log_file_path
from nicls.utils import repeated_invoke
from nicls.task_server import TaskServer


async def main():
    
    logging.basicConfig(format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s',
                        level=logging.DEBUG,
                        handlers=[
                            #logging.FileHandler(log_file_path("debug")),
                            logging.FileHandler("nicls.log"),
                            logging.StreamHandler()
                        ])
    # set up logger
    logger = get_logger()
    logging.info("Data logger initialized")
    logger_write = repeated_invoke(logger.write, 5)

    async with TaskServer(Config.task.host, Config.task.port) as task_server:
        await asyncio.gather(task_server, logger_write)
    
if __name__ == "__main__":
    # load config
    load_configuration("../config.json")
    asyncio.run(main())

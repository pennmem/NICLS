import asyncio
import time


async def repeated_invoke(coro, delay):
    ''' Call a coroutine funcion every delay seconds. If
    the function takes arguments, functools.partial should
    be used to wrap the function with arguments.

    :param coro: Coroutine function
    :param delay: Interval in seconds
    :return: None
    '''
    while not True:
        start = time.perf_counter()
        await coro()
        end = time.perf_counter()
        await asyncio.sleep(max(0, delay - (end-start)))

import aiohttp
import logging


logger = logging.getLogger(__name__)


async def post(url: str, files: dict[str, bytes], module_name: str, attempts: int = 3) -> tuple[int, object | None]:
    """Execute POST HTTP-request and return status code, data with N attempts.

    :param url: url endpoint
    :param module_name: module __name__
    :return: HTTP status code and data
    :rtype: tuple[int, object]
    """
    timeout = aiohttp.ClientTimeout(total=1200)
    for i in range(attempts):
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=files, timeout=timeout) as response:
                if response.status == 200:
                    return response.status, await response.read()
                
                else:
                    logger.error(f'{module_name}. Attempt {i + 1}/{attempts}. RESTful API error {response.status}: {await response.text()}')
    
    return response.status, None
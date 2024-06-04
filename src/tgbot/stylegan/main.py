import logging
from src.api import restful_api


def main():
    restful_api.fastapi_run()


if __name__ == '__main__':
    # Add logging
    file_handler = logging.FileHandler('stylegan.log', encoding='utf-8')
    stream_handler = logging.StreamHandler()
    logging.basicConfig(handlers=[file_handler, stream_handler],
                        level=logging.INFO,
                        format="[%(asctime)s: %(levelname)s: %(name)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

    main()
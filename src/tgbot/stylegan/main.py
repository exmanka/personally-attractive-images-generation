import logging
from src.api import restful_api


def main():
    restful_api.fastapi_run()


if __name__ == '__main__':
    # Add logging
    logging.basicConfig(handlers=[logging.FileHandler('algo.log'), logging.StreamHandler()],
                        level=logging.INFO,
                        format='[%(asctime)s: %(levelname)s: %(name)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        encoding='utf-8')

    main()
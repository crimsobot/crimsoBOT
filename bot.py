import logging

from config import LOG_LEVEL, TOKEN
from crimsobot.bot import CrimsoBOT


# it's go time
if __name__ == '__main__':
    # set log config
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)8s: %(message)s\t(%(name)s)',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=LOG_LEVEL
    )

    # instantiate the bot
    bot = CrimsoBOT()
    bot.load_extensions()

    bot.run(TOKEN)

import logging

import click

from config import LOG_LEVEL, TOKEN
from crimsobot.bot import CrimsoBOT

logging.basicConfig(
    format='[%(asctime)s] %(levelname)8s: %(message)s\t(%(name)s)',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=LOG_LEVEL
)


@click.group()
def cli():
    pass


@cli.command()
def run():
    """This command runs the bot."""

    bot = CrimsoBOT()
    bot.load_extensions()
    bot.run(TOKEN)


if __name__ == '__main__':
    cli()

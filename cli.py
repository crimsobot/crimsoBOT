import asyncio
import logging

import click

from config import LOG_LEVEL, TOKEN
from crimsobot import db
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


@cli.command()
def initdb():
    """This command initializes the database schemas."""

    click.secho('Creating tables...', bg='blue', fg='bright_white')

    loop = asyncio.get_event_loop()

    async def coro() -> None:
        await db.connect()
        await db.create_schemas(safe=False)

    try:
        loop.run_until_complete(coro())
    finally:
        loop.run_until_complete(db.close())

    click.secho('Done!', bg='green', fg='bright_white')


if __name__ == '__main__':
    cli()

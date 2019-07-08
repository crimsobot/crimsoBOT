import asyncio
import random
from typing import List

import aiofiles
import discord

from config import REMINDER_CHANNEL_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.utils.tools import clib_path_join


class Reminder:
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot
        self.bot.loop.create_task(self.send_reminder())

    async def send_reminder(self):
        """"Sends a disappearing random reminder in default channel."""

        await self.bot.wait_until_ready()

        reminder_list = await self._get_reminders()

        # send in current channel on startup, and then...
        while not self.bot.is_closed():
            # calc time to next msg
            time_until = int(random.gauss(900, 90))
            await asyncio.sleep(time_until)

            # then send to each channel in list
            for channel_id in REMINDER_CHANNEL_IDS:
                channel = self.bot.get_channel(channel_id)
                msg = await channel.send(random.choice(reminder_list))

                # delete after 10s if no reaction
                await asyncio.sleep(10)
                cache_msg = discord.utils.get(self.bot.cached_messages, id=msg.id)
                if not cache_msg.reactions:
                    await msg.delete()

    @staticmethod
    async def _get_reminders() -> List[str]:
        file = clib_path_join('text', 'reminders.txt')

        # open reminder text file, strip newlines at end
        async with aiofiles.open(file, encoding='utf-8', errors='ignore') as f:
            reminders = await f.readlines()

        reminders = [line[:-1] for line in reminders]
        reminders = [line.replace('\\n', '\n') for line in reminders]

        return reminders


def setup(bot: CrimsoBOT):
    Reminder(bot)

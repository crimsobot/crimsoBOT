import asyncio

from discord import Game

from crimsobot.bot import CrimsoBOT


class PresenceChanger:
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot
        self.bot.loop.create_task(self.change_presence())

    async def change_presence(self):
        """Slow scrolling effect for "Playing" status message."""

        await self.bot.wait_until_ready()

        # status to scroll (about 25 characters recommended)
        current_status = 'crimsoBOT is watching...'
        while not self.bot.is_closed():
            current_status = self._reorder_text(current_status)
            await self.bot.change_presence(activity=Game(current_status))
            await asyncio.sleep(7)

    @staticmethod
    def _reorder_text(string_in):
        """Reorders a string. Called iteratively to give scrolling effect."""

        string_out = string_in[1:] + string_in[0]
        return string_out


def setup(bot):
    PresenceChanger(bot)

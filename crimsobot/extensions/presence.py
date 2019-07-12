import asyncio

from discord import Game

from crimsobot.bot import CrimsoBOT


class PresenceChanger:
    def __init__(self, bot: CrimsoBOT) -> None:
        self.bot = bot
        self.bot.loop.create_task(self.change_presence())

        # status to scroll (about 25 characters recommended)
        self.current_status = 'crimsoBOT is watching...'

    async def change_presence(self) -> None:
        """Slow scrolling effect for "Playing" status message."""

        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.current_status = self._reorder_text(self.current_status)
            await self.bot.change_presence(activity=Game(self.current_status))
            await asyncio.sleep(7)

    @staticmethod
    def _reorder_text(text: str) -> str:
        """Reorders a string. Called iteratively to give scrolling effect."""

        return text[1:] + text[0]


def setup(bot: CrimsoBOT) -> None:
    PresenceChanger(bot)

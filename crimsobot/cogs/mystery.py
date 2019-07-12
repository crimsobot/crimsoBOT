import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import tarot


class Mystery(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.command(hidden=True)
    async def tarot(self, ctx: commands.Context, spread: str = 'ppf') -> None:
        """Tarot readings by crimsoBOT."""

        fp, descriptions = tarot.reading(spread)
        await ctx.send('\n'.join(descriptions), file=discord.File(fp, 'reading.png'))


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Mystery(bot))

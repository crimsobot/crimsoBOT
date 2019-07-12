import discord
from discord.ext import commands

from crimsobot.utils import tarot


class Mystery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def tarot(self, ctx, spread='ppf'):
        """Tarot readings by crimsoBOT."""

        fp, descriptions = tarot.reading(spread)
        await ctx.send('\n'.join(descriptions), file=discord.File(fp, 'reading.png'))


def setup(bot):
    bot.add_cog(Mystery(bot))

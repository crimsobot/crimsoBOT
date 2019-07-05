import discord
from discord.ext import commands
import discord.errors as de
from .clib import crimsotools as c
from .clib import crimsotarot as tarot


class Mystery:
    def __init__(self,bot):
        self.bot = bot

    @commands.command(pass_context=True, hidden=True)
    async def tarot(self, ctx, spread='ppf'):
        """Tarot readings by crimsoBOT."""
        descriptions = tarot.reading(spread)
        await self.bot.send_file(ctx.message.channel,
                                 c.clib_path_join('tarot', 'reading.png'),
                                 content='\n'.join(descriptions))

def setup(bot):
    bot.add_cog(Mystery(bot))

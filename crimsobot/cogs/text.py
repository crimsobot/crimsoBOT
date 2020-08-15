from typing import Optional

from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import text as texttools, tools as c
from crimsobot.utils.converters import AbsurdEmojiConverter


class Text(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.command()
    async def e(self, ctx: commands.Context, *, message: str) -> None:
        """Convert message to emojis. Character limit ~450."""

        message = texttools.block(message)
        lines = c.crimsplit(message, ' ', limit=1900)

        if len(lines) > 5:
            raise commands.CommandInvokeError('Too many lines.')

        for line in lines:
            await ctx.send(line)

    @commands.command()
    async def small(self, ctx: commands.Context, *, text: str) -> None:
        """Make text small!"""

        output = texttools.superscript(text)
        await ctx.send('{}: {}'.format(ctx.message.author.mention, output))

    @commands.command()
    async def flip(self, ctx: commands.Context, *, text: str) -> None:
        """Make text upside down!"""

        output = texttools.upsidedown(text)
        await ctx.send('{}: {}'.format(ctx.message.author.mention, output))

    @commands.command(aliases=['xokclock', 'xoktime', 'emojitime'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def emojiclock(self, ctx: commands.Context, emoji: Optional[AbsurdEmojiConverter], *, location: str) -> None:
        """Get the time at location (required) in emojis!"""

        emoji = str(emoji or '<:bedoclock:567167125807038464>')  # type: ignore

        # then check for these not-actually-emojis
        not_real_emojis = ['©', '®', '™']
        if emoji in not_real_emojis:
            await ctx.send("*Not a real emoji. (It's complicated.)*")
            return

        # send to helper function
        try:
            emoji_time_string = texttools.emojitime(emoji, location)
        except AttributeError:
            await ctx.send('`You must specify a location for local time!`')
            return

        # split long string
        lines = c.crimsplit(emoji_time_string, '\u2005', limit=1899)
        lines[-1] = lines[-1] + ' \u200B                      \u200B'
        for line in lines:
            await ctx.send(line)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Text(bot))

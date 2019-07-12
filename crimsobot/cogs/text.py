from discord.ext import commands

from crimsobot.utils import image as imagetools, text as texttools, tools as c


class Text(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def e(self, ctx, *, message):
        """Convert message to emojis. Character limit ~450."""

        message = texttools.block(message)
        lines = c.crimsplit(message, ' ', limit=1900)

        if len(lines) > 5:
            raise commands.CommandInvokeError('Too many lines.')

        for line in lines:
            await ctx.send(line)

    @commands.command()
    async def small(self, ctx, *, text):
        """Make text small!"""

        output = texttools.superscript(text)
        await ctx.send('{}: {}'.format(ctx.message.author.mention, output))

    @commands.command()
    async def flip(self, ctx, *, text):
        """Make text upside down!"""

        output = texttools.upsidedown(text)
        await ctx.send('{}: {}'.format(ctx.message.author.mention, output))

    @commands.command(aliases=['xokclock', 'xoktime', 'emojitime'])
    async def emojiclock(self, ctx, emoji, *args):
        """Get the time at location (required) in emojis!"""

        # input parser
        emoji = args[0]
        location_args = args[1:]

        # if an emoji was not specified by user, bigmoji() returns (False, False)
        emoji_check, _ = imagetools.bigmoji(emoji)
        if not emoji_check:
            # if no emoji specified, then input "emoji" is actually first word of location
            emoji = '<:xok:563825728102334465>'  # default to xok emoji in crimsoBOT server
            location_args = args

        location = ' '.join(location_args)  # location from tuple to string

        # then check for these not-actually-emojis
        not_real_emojis = ['©', '®', '™']
        for emj in not_real_emojis:
            if emj == emoji:
                await ctx.send("*Not a real emoji. (It's complicated.)*")
                return

        # send to helper function
        try:
            emoji_time_string = texttools.emojitime(emoji, location)
        except AttributeError:
            await ctx.send('`You must specify a location for local time!`')
            return

        # split long string
        emoji_time_string = c.crimsplit(emoji_time_string, '\u2005', limit=1899)
        emoji_time_string[-1] = emoji_time_string[-1] + ' \u200B                      \u200B'
        for line in emoji_time_string:
            await ctx.send(line)


def setup(bot):
    bot.add_cog(Text(bot))

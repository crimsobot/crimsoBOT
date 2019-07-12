from discord.ext import commands

from crimsobot.utils import image as imagetools, text as texttools, tools as c


class Text(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def e(self, ctx, *args):
        """Convert message to emojis. Character limit ~450."""

        string_in = ' '.join(args)
        output = texttools.block(string_in)
        output = c.crimsplit(output, ' ', limit=1900)

        if len(output) <= 5:
            for message in output:
                await ctx.send(message)
        else:
            return commands.CommandInvokeError('>e: too long')

    @commands.command()
    async def small(self, ctx, *, arg):
        """Make text small!"""

        output = texttools.superscript(arg)
        await ctx.send('{}: {}'.format(ctx.message.author.mention, output))

    @commands.command()
    async def flip(self, ctx, *, arg):
        """Make text upside down!"""

        output = texttools.upsidedown(arg)
        await ctx.send('{}: {}'.format(ctx.message.author.mention, output))

    @commands.command(aliases=['xokclock', 'xoktime', 'emojitime'])
    async def emojiclock(self, ctx, emoji, *location):
        """Get the time at location (required) in emojis!"""

        # input parser
        # if an emoji was not specified by user, bigmoji() returns (False, False)
        emoji_check, _ = imagetools.bigmoji(emoji)
        if emoji_check is False:
            # if no emoji specified, then input "emoji" is actually first word of location
            location = [emoji, ' '.join(location)]
            emoji = '<:xok:563825728102334465>'  # default to xok emoji in crimsoBOT server

        location = ' '.join(location)  # location from tuple to string

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

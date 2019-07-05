import discord
from discord.ext import commands
import asyncio
from .clib import crimsotools as c
from .clib import texttools as texttools
from .clib import imagetools as imagetools

# lists for games in progress
eface_channels = []


class Text:
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def e(self, *args):
        """Convert message to emojis. Character limit ~450."""
        string_in = ' '.join(args)
        output = texttools.block(string_in)
        output = c.crimsplit(output, ' ', limit=1900)
        if len(output) <= 5:
            for message in output:
                await self.bot.say(message)
        else:
            return commands.CommandInvokeError('>e: too long')

    @commands.command(pass_context=True)
    async def small(self, ctx, *, arg):
        """Make text small!"""
        output = texttools.superscript(arg)
        await self.bot.say('{}: {}'.format(ctx.message.author.mention,output))

    @commands.command(pass_context=True)
    async def flip(self, ctx, *, arg):
        """Make text upside down!"""
        output = texttools.upsidedown(arg)
        await self.bot.say('{}: {}'.format(ctx.message.author.mention,output))

    @commands.command(pass_context=True,
                      aliases=['xokclock', 'xoktime', 'emojitime'])
    async def emojiclock(self, ctx, emoji, *location):
    # ocation, emoji='<:xok:551174281367650356>'):
        """Get the time at location (required) in emojis!"""
        # input parser
        emoji_specified = True
        try:
            open(imagetools.bigmoji(emoji))
        except FileNotFoundError:
            emoji_specified = False
        except OSError: # not a path; a URL!
            if emoji.startswith('<'):
                pass
        if not emoji_specified:
            location = [emoji, ' '.join(location)]
            emoji = '<:xok:551174281367650356>'
        location = ' '.join(location)
        # then check for these not-actually-emojis
        not_real_emojis = ['©', '®', '™']
        for emj in not_real_emojis:
            if emj == emoji:
                await self.bot.say('*Not a real emoji. (It\'s complicated.)*')
                return
        # check emoji now that input is parsed just to make sure an emoji was valid (still necessary?)
        if (emoji.startswith('<:') or emoji.startswith('<a:')) is False:
            try:
                open(imagetools.bigmoji(emoji), 'rb')
            except:
                await self.bot.say('*Not a valid emoji.*')
                return
        try:
            emoji_time_string = texttools.emojitime(emoji, location)
        except AttributeError:
            await self.bot.say('`You must specify a location for local time!`')
            return
        # split long string
        emoji_time_string = c.crimsplit(emoji_time_string, '\u2005', limit=1899)
        emoji_time_string[-1] = emoji_time_string[-1] + ' \u200B                      \u200B'
        for line in emoji_time_string:
            await self.bot.say(line)

def setup(bot):
    bot.add_cog(Text(bot))

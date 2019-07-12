import asyncio
import logging

import discord
from discord.ext import commands

from config import ADMIN_USER_IDS
from crimsobot.utils import image as imagetools, tools as c

log = logging.getLogger(__name__)

# lists for games in progress
emoji_channels = []


class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Boop the snoot! Must mention someone to boop.')
    async def boop(self, ctx, mention):
        booper = str(ctx.message.author.nick)
        if booper == 'None':
            booper = str(ctx.message.author.name)
        if mention.startswith('<@'):
            mention = str(ctx.message.mentions[0].nick)
            if mention == 'None':
                mention = str(ctx.message.mentions[0].name)

            imagetools.boop(booper, mention)
            await ctx.send(file=discord.File(c.clib_path_join('img', 'booped.jpg'), 'boop.jpg'))

    @commands.command(aliases=['emojimage', 'eimg2'])
    @commands.cooldown(1, 72, commands.BucketType.user)
    async def eimg(self, ctx, image=None):
        """
        Convert image to emojis with a bit more detail!
        WARNING: Best on desktop. You will get a LOT of PMs. SVGs are no.
        Works best with images with good contrast and larger features.
        A one-pixel-wide line is likely not going to show up in the final product.
        """

        line_list = imagetools.make_emoji_image_v3(ctx, image)
        c.checkin('eimg', ctx.message.guild, ctx.message.author, emoji_channels)

        # send line-by-line as DM
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(0.72)

        c.checkout('eimg', ctx.message.guild, ctx.message.author, emoji_channels)

    @commands.command(hidden=True)
    @commands.cooldown(1, 4 * 60 * 60, commands.BucketType.user)
    async def bless(self, ctx):
        """bless bless"""

        # read in lines of emojis
        line_list = open(c.clib_path_join('img', 'bless.txt'),
                         encoding='utf8',
                         errors='ignore').readlines()

        # check-in
        c.checkin('bless', ctx.message.guild, ctx.message.author, emoji_channels)

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(1)

        c.checkout('bless', ctx.message.guild, ctx.message.author, emoji_channels)

    @commands.command(hidden=True)
    async def eface_pm(self, ctx, userid, *, arg):
        """crimsoBOT avatar as emojis!"""

        if ctx.message.author.id not in ADMIN_USER_IDS:
            return

        # get user object
        user = await self.bot.fetch_user(userid)

        # read in lines of emojis
        line_list = open(c.clib_path_join('text', 'emojiface.txt'),
                         encoding='utf8',
                         errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]
        line_list = line_list[0:-1]

        # send line-by-line as DM
        for line in line_list:
            await user.send(line)
            await asyncio.sleep(1)

        await user.send(arg)

    @commands.command(hidden=True)
    @commands.cooldown(1, 8 * 60 * 60, commands.BucketType.user)
    async def eface(self, ctx):
        """crimsoBOT avatar as emojis!"""

        c.checkin('eface', ctx.message.guild, ctx.message.author, emoji_channels)

        # read in lines of emojis
        line_list = open(c.clib_path_join('text', 'emojiface.txt'), encoding='utf8', errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(1)

        c.checkout('eface', ctx.message.guild, ctx.message.author, emoji_channels)

    @commands.command()
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def acidify(self, ctx, number_of_hits, image=None):
        """1-3 hits only. Can use image link, attachment, mention, or emoji."""

        # exception handling
        try:
            if not 1 <= int(number_of_hits) <= 3:
                raise ValueError
        except ValueError:
            raise commands.CommandInvokeError('not 1-3 hits')

        log.info('acidify running on %s/%s...', ctx.message.guild, ctx.message.channel)

        filename = imagetools.acid(ctx, int(number_of_hits), image)

        # pluralize 'hit' if need be
        ess = '' if int(number_of_hits) == 1 else 's'
        await ctx.send('**{} hit{}:**'.format(number_of_hits, ess), file=discord.File(filename))

        log.info('acidify COMPLETE on %s/%s!', ctx.message.guild, ctx.message.channel)

    @commands.command(hidden=True)
    async def inspect(self, ctx, user_id=None):
        if ctx.message.author.id not in ADMIN_USER_IDS:
            return

        # read in lines of emojis
        line_list = open(c.clib_path_join('games', 'emojilist.txt'),
                         encoding='utf8',
                         errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        if user_id is not None:
            user = await self.bot.fetch_user(user_id)
        else:
            user = ctx.message.author

        log.info('%s is using inspect...', user)

        for line in line_list:
            await user.send(line)
            await asyncio.sleep(1)

        log.info("%s's inspection is done!", user)

    @commands.command()
    async def needping(self, ctx, image=None):
        """SOMEONE needs PING. User mention, attachment, link, or emoji."""

        imagetools.fishe(ctx, image)
        await ctx.send(file=discord.File(c.clib_path_join('img', 'needping.png'), 'needping.png'))

    @commands.command()
    async def needban(self, ctx, image=None):
        """SOMEONE needs BAN. User mention, attachment, link, or emoji."""

        imagetools.ban_overlay(ctx, image)
        await ctx.send(file=discord.File(c.clib_path_join('img', 'needban.png'), 'needban.png'))

    @commands.command()
    async def xokked(self, ctx, image=None):
        """Get xokked! User mention, attachment, link, or emoji."""

        filename = imagetools.xok(ctx, image)
        await ctx.send(file=discord.File(filename, 'xokked.png'))

    @commands.command(aliases=['pingbadge'])
    async def verpingt(self, ctx, image=None):
        """Add Discord notification badge to an image."""

        if image is None:
            try:
                ctx.message.attachments[0].url
            except IndexError:
                raise commands.MissingRequiredArgument('no')

        thumb = 'https://emojipedia-us.s3.amazonaws.com/thumbs/120/twitter/185/input-symbol-for-numbers_1f522.png'
        embed = c.crimbed('Choose a corner:', '1. Top left\n2. Top right\n3. Bottom left\n4. Bottom right', thumb)
        prompt = await ctx.send(embed=embed)

        # define check for position vote
        def check(msg):
            try:
                valid_choice = 0 < int(msg.content) <= 4
                in_channel = msg.channel == ctx.message.channel
                is_author = msg.author == ctx.message.author
                return valid_choice and in_channel and is_author
            except ValueError:
                return False

        # define default position, listen for user to specify different one
        msg = await self.bot.wait_for('message', check=check, timeout=15)
        if msg is None:
            position = '4'
        else:
            position = msg.content

        # send to pingbadge
        imagetools.pingbadge(ctx, image, position)

        # delete prompt and vote, send image
        if msg is not None:
            await msg.delete()
        await prompt.delete()
        await ctx.send(file=discord.File(c.clib_path_join('img', 'pingbadge.png'), 'verpingt.png'))


def setup(bot):
    bot.add_cog(Image(bot))

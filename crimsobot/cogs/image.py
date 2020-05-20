import asyncio
import logging
from typing import List, Optional

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import image as imagetools, tools as c

log = logging.getLogger(__name__)

# lists for games in progress
emoji_channels = []  # type: List[int]


class Image(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.command(aliases=['acidify'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def acid(self, ctx: commands.Context, number_of_hits: int, image: Optional[str] = None) -> None:
        """1-3 hits only. Can use image link, attachment, mention, or emoji."""

        # exception handling
        if not 1 <= number_of_hits <= 3:
            raise commands.BadArgument('Number of hits is out of bounds.')

        fp, img_format = await imagetools.process_image(ctx, image, 'acid', number_of_hits)
        if fp is None:
            return

        # pluralize 'hit' if need be
        ess = '' if number_of_hits == 1 else 's'
        await ctx.send('**{} hit{}:**'.format(number_of_hits, ess),
                       file=discord.File(fp, 'acid.{}'.format(img_format.lower())))

    @commands.command(hidden=True)
    async def aenima(self, ctx: commands.Context, image: Optional[str] = None) -> None:

        fp, img_format = await imagetools.process_image(ctx, image, 'aenima')
        if fp:
            await ctx.send(file=discord.File(fp, 'aenima.{}'.format(img_format.lower())))

    @commands.command(hidden=True)
    @commands.cooldown(1, 4 * 60 * 60, commands.BucketType.user)
    async def bless(self, ctx: commands.Context) -> None:
        """bless bless"""

        # read in lines of emojis
        line_list = open(c.clib_path_join('img', 'bless.txt'), encoding='utf8', errors='ignore').readlines()

        # check-in
        chk = c.checkin(ctx.message.author, emoji_channels)
        if chk is False:
            await ctx.send('`no!`')
            return

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(1)

        c.checkout(ctx.message.author, emoji_channels)

    @commands.command(brief='Boop the snoot! Must mention someone to boop.')
    async def boop(self, ctx: commands.Context, mention: discord.Member) -> None:
        fp = imagetools.make_boop_img(ctx.author.display_name, mention.display_name)
        await ctx.send(file=discord.File(fp, 'boop.jpg'))

    @commands.command(hidden=True)
    @commands.cooldown(1, 8 * 60 * 60, commands.BucketType.user)
    async def eface(self, ctx: commands.Context) -> None:
        """crimsoBOT avatar as emojis!"""

        chk = c.checkin(ctx.message.author, emoji_channels)
        if chk is False:
            await ctx.send('`no!`')
            return

        # read in lines of emojis
        line_list = open(c.clib_path_join('text', 'emojiface.txt'), encoding='utf8', errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(1)

        c.checkout(ctx.message.author, emoji_channels)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def eface_pm(self, ctx: commands.Context, user: discord.User, *, message: str) -> None:
        """crimsoBOT avatar as emojis!"""

        # read in lines of emojis
        line_list = open(c.clib_path_join('text', 'emojiface.txt'), encoding='utf8', errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]
        line_list = line_list[0:-1]

        # send line-by-line as DM
        for line in line_list:
            await user.send(line)
            await asyncio.sleep(1)

        await user.send(message)

    @commands.command(aliases=['emojimage', 'eimg2'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def eimg(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """
        Convert image to emojis with a bit more detail!
        WARNING: Best on desktop. You will get a LOT of PMs. SVGs are no.
        Works best with images with good contrast and larger features.
        A one-pixel-wide line is likely not going to show up in the final product.
        """

        line_list = await imagetools.make_emoji_image(ctx, image)
        chk = c.checkin(ctx.message.author, emoji_channels)
        if chk is False:
            await ctx.send('`no!`')
            return

        # send line-by-line as DM
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(0.72)

        c.checkout(ctx.message.author, emoji_channels)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def inspect(self, ctx: commands.Context, user: Optional[discord.User] = None) -> None:
        # read in lines of emojis
        line_list = open(c.clib_path_join('games', 'emojilist.txt'), encoding='utf8', errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        if not user:
            user = ctx.message.author

        for line in line_list:
            await user.send(line)
            await asyncio.sleep(1)

    @commands.command(hidden=True)
    async def lateralus(self, ctx: commands.Context, image: Optional[str] = None) -> None:

        fp, img_format = await imagetools.process_image(ctx, image, 'lateralus')
        if fp:
            await ctx.send(file=discord.File(fp, 'lateralus.{}'.format(img_format.lower())))

    @commands.command()
    async def needban(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """SOMEONE needs BAN. User mention, attachment, link, or emoji."""

        fp, img_format = await imagetools.process_image(ctx, image, 'needban')
        if fp:
            await ctx.send(file=discord.File(fp, 'needban.{}'.format(img_format.lower())))

    @commands.command()
    async def needping(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """SOMEONE needs PING. User mention, attachment, link, or emoji."""

        fp, img_format = await imagetools.process_image(ctx, image, 'needping')
        if fp:
            await ctx.send(file=discord.File(fp, 'needping.{}'.format(img_format.lower())))

    @commands.command(aliases=['verpingt'])
    async def pingbadge(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """Add Discord notification badge to an image."""

        if image is None:
            try:
                ctx.message.attachments[0].url
            except IndexError:
                raise commands.MissingRequiredArgument('no')

        embed = c.crimbed(
            title='Choose a corner:',
            descr='\n'.join([
                '1. Top left',
                '2. Top right',
                '3. Bottom left',
                '4. Bottom right',
            ]),
            thumb_name='https://i.imgur.com/cgGKghX.png',
        )
        prompt = await ctx.send(embed=embed)

        # define check for position vote
        def check(msg: discord.Message) -> bool:
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
            position = 4
        else:
            position = int(msg.content)

        # send to pingbadge
        fp, img_format = await imagetools.process_image(ctx, image, 'pingbadge', position)
        if fp is None:
            return

        # delete prompt and vote, send image
        if msg is not None:
            await msg.delete()
        await prompt.delete()
        await ctx.send(file=discord.File(fp, 'verpingt.{}'.format(img_format.lower())))

    @commands.command()
    async def xokked(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """Get xokked! User mention, attachment, link, or emoji."""

        fp, img_format = await imagetools.process_image(ctx, image, 'xokked')
        if fp:
            await ctx.send(file=discord.File(fp, 'xokked.{}'.format(img_format.lower())))


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Image(bot))

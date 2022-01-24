import asyncio
import logging
import random
from datetime import datetime
from typing import Callable, Optional

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import image as imagetools, tools as c

log = logging.getLogger(__name__)

eface_bucket = commands.MaxConcurrency(1, per=commands.BucketType.user, wait=False)


def shared_max_concurrency(bucket: commands.MaxConcurrency) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        if isinstance(func, commands.Command):
            func._max_concurrency = bucket
        else:
            func.__commands_max_concurrency__ = bucket  # type: ignore
        return func
    return decorator


class Image(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    async def get_image_and_embed(self, ctx: commands.Context, image: Optional[str], effect: str,
                                  arg: Optional[int], title: str) -> None:
        """Get image, construct and send embed with result."""
        # process image
        fp, img_format = await imagetools.process_image(ctx, image, effect, arg)
        # if (None, None) is returned from process_image(), then the user has already been informed of issue
        if fp is None:
            return

        # filename and file
        filename = '{}{}.{}'.format(effect, datetime.utcnow().strftime('%Y%m%d%H%M%S'), img_format.lower())
        f = discord.File(fp, filename)

        embed = c.crimbed(
            title=title,
            descr=None,
            attachment=filename,
            footer='Requested by {}'.format(ctx.author),
        )

        await ctx.send(file=f, embed=embed)

    @commands.command(aliases=['acidify'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @shared_max_concurrency(eface_bucket)
    async def acid(self, ctx: commands.Context, number_of_hits: int, image: Optional[str] = None) -> None:
        """1-3 hits only. Can use image link, attachment, mention, or emoji."""

        # exception handling
        if not 1 <= number_of_hits <= 3:
            raise commands.BadArgument('Number of hits is out of bounds.')

        effect = 'acid'
        ess = '' if number_of_hits == 1 else 's'
        title = '{}: {} hit{}'.format(effect.upper(), number_of_hits, ess)
        await self.get_image_and_embed(ctx, image, effect, number_of_hits, title)

    @commands.command(hidden=True)
    async def aenima(self, ctx: commands.Context, image: Optional[str] = None) -> None:

        effect = 'aenima'
        title = random.choice([
            'Constant overstimulation', 'Not enough, I need more', "I'll keep digging",
            'He had a lot of nothing to say', 'Ranting and pointing his finger', 'So long, we wish you well',
            "What's coming through is alive", 'Consideratly killing me', 'I am too connected to you',
            'Insecure delusions', 'Change is coming', 'Crawling on my belly',
            'Figlio di puttana', "You think you're cool, right?", "You know I'm involved with black magic?",
            'Vans, 501s, and a dope Beastie T', "I've got some ad-vice for you little buddy", 'Send more money',
            'Eleven is standing still', 'Moving me with a sound', 'Under a dead Ohio Sky',
            'Ein halbes Pfund Butter', 'Ein wenig extra Staußzucker', 'Und keine Eier',
            'Saw the gap again today', "I am somewhere I don't wanna be", 'It will end no other way',
            'Hey. Hey. Hey. Hey. Hey', 'Some say the end is near', 'Fret for your latte',
            'Dreaming of that fix again', 'So good to see you once again', 'Blue as our new second sun'
        ])
        await self.get_image_and_embed(ctx, image, effect, None, title)

    @commands.command(hidden=True)
    @commands.cooldown(1, 4 * 60 * 60, commands.BucketType.user)
    @shared_max_concurrency(eface_bucket)
    async def bless(self, ctx: commands.Context) -> None:
        """bless bless"""

        # read in lines of emojis
        line_list = open(c.clib_path_join('img', 'bless.txt'), encoding='utf8', errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(1)

    @commands.command(brief='Boop the snoot! Must mention someone to boop.')
    async def boop(self, ctx: commands.Context, mention: discord.Member) -> None:
        fp = await imagetools.make_boop_img(ctx.author.display_name, mention.display_name)

        # filename and file
        filename = '{}{}.png'.format('boop', datetime.utcnow().strftime('%Y%m%d%H%M%S'))
        f = discord.File(fp, filename)

        embed = c.crimbed(
            title='{} booped {}!'.format(ctx.author, mention),
            descr=None,
            attachment=filename,
        )

        await ctx.send(file=f, embed=embed)

    @commands.command(hidden=True)
    @commands.cooldown(1, 8 * 60 * 60, commands.BucketType.user)
    @shared_max_concurrency(eface_bucket)
    async def eface(self, ctx: commands.Context) -> None:
        """crimsoBOT avatar as emojis!"""

        # read in lines of emojis
        line_list = open(c.clib_path_join('text', 'emojiface.txt'), encoding='utf8', errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(1)

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
    @shared_max_concurrency(eface_bucket)
    async def eimg(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """
        Convert image to emojis with a bit more detail!
        WARNING: Best on desktop. You will get a LOT of PMs. SVGs are no.
        Works best with images with good contrast and larger features.
        A one-pixel-wide line is likely not going to show up in the final product.
        """

        line_list = await imagetools.make_emoji_image(ctx, image)

        # send line-by-line as DM
        for line in line_list:
            await ctx.message.author.send(line)
            await asyncio.sleep(0.72)

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

        effect = 'lateralus'
        title = random.choice([
            'Saturn ascends', 'Clutch it like a cornerstone', 'Wear the grudge like a crown',
            "But I'm still right here", 'Gonna wait it out', 'I must keep reminding myself of this',
            'I know the pieces fit', 'Finding beauty in the dissonance', 'Between supposed lovers',
            'So familiar and overwhelmingly warm', 'Embrancing you, this reality here', 'So wide eyed and hopeful',
            'This holy reality', 'All this pain is an illusion', 'Recoginize this as a holy gift',
            'Fat little parasite', 'Suck me dry', 'I hope you choke on this',
            'Reaching out to embrace the random', 'Witness the beauty', 'Spiral out',
            'Mention this to me', 'Mention something, mention anything', 'Watch the weather change',
            'My self-indulgent pitiful hole', "It's calling me...", 'Before I pine away...',
            "I don't have a whole lot of time", "They'll triangulate on this position really soon",
            "What we're thinking of as aliens⁠—they're extradimensional beings..."
        ])
        await self.get_image_and_embed(ctx, image, effect, None, title)

    @commands.command()
    async def needban(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """SOMEONE needs BAN. User mention, attachment, link, or emoji."""

        effect = 'needban'
        title = 'Need ban?'
        await self.get_image_and_embed(ctx, image, effect, None, title)

    @commands.command()
    async def needping(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """SOMEONE needs PING. User mention, attachment, link, or emoji."""

        effect = 'needping'
        title = 'Need ping?'
        await self.get_image_and_embed(ctx, image, effect, None, title)

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

        # delete prompt and vote, send image
        if msg is not None:
            await msg.delete()
        await prompt.delete()

        effect = 'pingbadge'
        title = 'verpingt!'
        await self.get_image_and_embed(ctx, image, effect, position, title)

    @commands.command()
    async def xokked(self, ctx: commands.Context, image: Optional[str] = None) -> None:
        """Get xokked! User mention, attachment, link, or emoji."""

        effect = 'xokked'
        title = '<:xok:563825728102334465>'
        await self.get_image_and_embed(ctx, image, effect, None, title)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Image(bot))

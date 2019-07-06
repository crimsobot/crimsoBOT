import asyncio

from discord.ext import commands

import crimsobot.utils.image as imagetools
import crimsobot.utils.tools as c

# lists for games in progress
emoji_channels = []


class Image:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, brief='Boop the snoot! Must mention someone to boop.')
    async def boop(self, ctx, mention):
        booper = str(ctx.message.author.nick)
        if booper == 'None':
            booper = str(ctx.message.author.name)
        if mention.startswith('<@'):
            mention = str(ctx.message.mentions[0].nick)
            if mention == 'None':
                mention = str(ctx.message.mentions[0].name)

            imagetools.boop(booper, mention)
            await self.bot.send_file(ctx.message.channel, c.clib_path_join('img', 'booped.jpg'))

    @commands.command(pass_context=True)
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def eimg(self, ctx, image=None):
        """
        Convert image to emojis!
        WARNING: Best on desktop. You will get a LOT of PMs. SVGs are no.
        Works best with images with good contrast and larger features.
        A one-pixel-wide line is likely not going to show up in the final product.
        Try >eimg2 if you want to preserve more detail.
        """

        await self.bot.send_message(ctx.message.author, 'Please wait...')

        imagetools.make_emoji_image(ctx, image)
        c.checkin('eimg', ctx.message.server, ctx.message.author, emoji_channels)
        await asyncio.sleep(10)

        # read in lines of emojis
        line_list = open(c.clib_path_join('img', 'emoji.txt'),
                         encoding='utf8',
                         errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        for line in line_list:
            await self.bot.send_message(ctx.message.author, line)
            await asyncio.sleep(1)

        c.checkout('eimg', ctx.message.server, ctx.message.author, emoji_channels)

    @commands.command(pass_context=True)
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def eimg2(self, ctx, image=None):
        """
        Convert image to emojis with a bit more detail!
        WARNING: Best on desktop. You will get a LOT of PMs. SVGs are no.
        Works best with images with good contrast and larger features.
        A one-pixel-wide line is likely not going to show up in the final product.
        """

        await self.bot.send_message(ctx.message.author, 'Please wait...')

        imagetools.make_emoji_image_v2(ctx, image)
        c.checkin('eimg2', ctx.message.server, ctx.message.author, emoji_channels)
        await asyncio.sleep(10)

        # read in lines of emojis
        line_list = open(c.clib_path_join('img', 'emoji.txt'),
                         encoding='utf8',
                         errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        for line in line_list:
            await self.bot.send_message(ctx.message.author, line)
            await asyncio.sleep(1)

        c.checkout('eimg2', ctx.message.server, ctx.message.author, emoji_channels)

    @commands.command(pass_context=True, hidden=True)
    @commands.cooldown(1, 4 * 60 * 60, commands.BucketType.user)
    async def bless(self, ctx):
        """bless bless"""

        # read in lines of emojis
        line_list = open(c.clib_path_join('img', 'bless.txt'),
                         encoding='utf8',
                         errors='ignore').readlines()

        # check-in
        c.checkin('bless', ctx.message.server, ctx.message.author, emoji_channels)

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        for line in line_list:
            await self.bot.send_message(ctx.message.author, line)
            await asyncio.sleep(1)

        c.checkout('bless', ctx.message.server, ctx.message.author, emoji_channels)

    @commands.command(pass_context=True, hidden=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def gimme_last(self, ctx):
        await self.bot.send_message(ctx.message.author, 'Last eimg:')

        # read in lines of emojis
        line_list = open(c.clib_path_join('img', 'emoji.txt'),
                         encoding='utf8',
                         errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        c.botlog('{} is using gimme_last...'.format(ctx.message.author))

        for line in line_list:
            await self.bot.send_message(ctx.message.author, line)
            await asyncio.sleep(1)

        c.botlog("{}'s gimme_last is done!".format(ctx.message.author))

    @commands.command(pass_context=True, hidden=True)
    async def eface_pm(self, ctx, userid, *, arg):
        """crimsoBOT avatar as emojis!"""

        if ctx.message.author.id == '310618614497804289':
            # get user object
            user = await self.bot.get_user_info(userid)

            # read in lines of emojis
            line_list = open(c.clib_path_join('text', 'emojiface.txt'),
                             encoding='utf8',
                             errors='ignore').readlines()

            # strip newlines
            line_list = [line.replace('\n', '') for line in line_list]
            line_list = line_list[0:-1]

            # send line-by-line as DM
            for line in line_list:
                await self.bot.send_message(user, line)
                await asyncio.sleep(1)

            await self.bot.send_message(user, arg)

    @commands.command(pass_context=True, hidden=True)
    @commands.cooldown(1, 8 * 60 * 60, commands.BucketType.user)
    async def eface(self, ctx):
        """crimsoBOT avatar as emojis!"""

        c.checkin('eface', ctx.message.server, ctx.message.author, emoji_channels)

        # read in lines of emojis
        line_list = open(c.clib_path_join('text', 'emojiface.txt'), encoding='utf8', errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]
        for line in line_list:
            await self.bot.send_message(ctx.message.author, line)
            await asyncio.sleep(1)

        c.checkout('eface', ctx.message.server, ctx.message.author, emoji_channels)

    @commands.command(pass_context=True)
    @commands.cooldown(2, 10, commands.BucketType.server)
    async def acidify(self, ctx, number_of_hits, image=None):
        """1-3 hits only. Can use image link, attachment, mention, or emoji."""

        # exception handling
        try:
            if not 1 <= int(number_of_hits) <= 3:
                raise ValueError
        except ValueError:
            raise commands.CommandInvokeError('not 1-3 hits')

        print('----IN PROGRESS---- | acidify running on {}/{}...'.format(ctx.message.server, ctx.message.channel))

        filename = imagetools.acid(ctx, int(number_of_hits), image)

        # pluralize 'hit' if need be
        ess = '' if int(number_of_hits) == 1 else 's'
        await self.bot.send_file(ctx.message.channel, filename, content='**{} hit{}:**'.format(number_of_hits, ess))

        c.botlog('acidify COMPLETE on {}/{}!'.format(ctx.message.server, ctx.message.channel))

    @commands.command(pass_context=True, hidden=True)
    async def inspect(self, ctx, user_id=None):
        if ctx.message.author.id != '310618614497804289':
            return

        # read in lines of emojis
        line_list = open(c.clib_path_join('games', 'emojilist.txt'),
                         encoding='utf8',
                         errors='ignore').readlines()

        # strip newlines
        line_list = [line.replace('\n', '') for line in line_list]

        # send line-by-line as DM
        if user_id is not None:
            user = await self.bot.get_user_info(user_id)
        else:
            user = ctx.message.author

        c.botlog('{} is using inspect...'.format(user))

        for line in line_list:
            await self.bot.send_message(user, line)
            await asyncio.sleep(1)

        c.botlog("{}'s inspection is done!".format(user))

    @commands.command(pass_context=True)
    async def needping(self, ctx, image=None):
        """SOMEONE needs PING. User mention, attachment, link, or emoji."""

        imagetools.fishe(ctx, image)
        await self.bot.send_file(ctx.message.channel, c.clib_path_join('img', 'needping.png'))

    @commands.command(pass_context=True)
    async def needban(self, ctx, image=None):
        """SOMEONE needs BAN. User mention, attachment, link, or emoji."""

        imagetools.ban_overlay(ctx, image)
        await self.bot.send_file(ctx.message.channel, c.clib_path_join('img', 'needban.png'))

    @commands.command(pass_context=True)
    async def xokked(self, ctx, image=None):
        """Get xokked! User mention, attachment, link, or emoji."""

        filename = imagetools.xok(ctx, image)
        await self.bot.send_file(ctx.message.channel, filename)

    @commands.command(pass_context=True,
                      aliases=['pingbadge'])
    async def verpingt(self, ctx, image=None):
        """Add Discord notification badge to an image."""

        if image is None:
            try:
                ctx.message.attachments[0]['url']
            except IndexError:
                raise commands.MissingRequiredArgument('no')

        thumb = 'https://emojipedia-us.s3.amazonaws.com/thumbs/120/twitter/185/input-symbol-for-numbers_1f522.png'
        embed = c.crimbed('Choose a corner:', '1. Top left\n2. Top right\n3. Bottom left\n4. Bottom right', thumb)
        prompt = await self.bot.send_message(ctx.message.channel, embed=embed)

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
        msg = await self.bot.wait_for_message(timeout=15, check=check)
        if msg is None:
            position = '4'
        else:
            position = msg.content

        # send to pingbadge
        imagetools.pingbadge(ctx, image, position)

        # delete prompt and vote, send image
        if msg is not None:
            await self.bot.delete_message(msg)
        await self.bot.delete_message(prompt)
        await self.bot.send_file(ctx.message.channel, c.clib_path_join('img', 'pingbadge.png'))


def setup(bot):
    bot.add_cog(Image(bot))

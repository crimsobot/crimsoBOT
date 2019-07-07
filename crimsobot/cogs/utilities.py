import logging

import discord
from discord.ext import commands

import crimsobot.utils.astronomy as astronomy
import crimsobot.utils.image as imagetools
import crimsobot.utils.tools as c

log = logging.getLogger(__name__)


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def ping(self, ctx):
        """Need ping? 10s cooldown after use."""

        msg = await ctx.send('<:ping:569954524932997122>...')
        time_in = ctx.message.created_at
        time_out = msg.created_at
        ping = (time_out - time_in).microseconds / 1000
        await msg.edit(content='<:ping:569954524932997122>...{:d}ms'.format(int(ping)))

    @commands.command()
    async def color(self, ctx, hex_value):
        """Get color sample from hex value."""

        imagetools.make_color_img(str(hex_value))
        await ctx.send(
            '**' + hex_value + '**',
            file=discord.File(
                c.clib_path_join('img', 'color.jpg'),
                'color.jpg'
            )
        )

    @commands.command()
    @commands.cooldown(2, 8, commands.BucketType.guild)
    async def palette(self, ctx, number_of_colors, link=None):
        """
        Get an image's main colors! Specify # of colors (1-10).
        • Must follow >palette with an integer between 1 and 10 then either an attached image or a link to an image.
        • Best results typically around 5 colors.
        • SVGs are no.
        • Images with transparency will sometimes produce a less-than-stellar palette.
        """

        log.info('palette running on %s/%s...', ctx.message.guild, ctx.message.channel)

        try:
            if not 1 <= int(number_of_colors) <= 10:
                raise ValueError
        except ValueError:
            return commands.CommandInvokeError(False)

        hex_color = imagetools.get_image_palette(ctx, int(number_of_colors), link)
        await ctx.send(
            '**Resampled image:**',
            file=discord.File(
                c.clib_path_join('img', 'resample.png'),
                'resample.png'
            )
        )
        await ctx.send(
            '**' + hex_color.upper() + '**',
            file=discord.File(
                c.clib_path_join('img', 'mosaic.png'),
                'mosaic.png'
            )
        )

        log.info('palette COMPLETE on %s/%s!', ctx.message.guild, ctx.message.channel)

    @commands.command(hidden=True)
    async def dearcrimso(self, ctx, *, arg):
        """Leave a message in crimso's inbox. Spam = ban"""

        if ctx.message.guild is not None:
            guild = str(ctx.message.guild.name)
            channel = str(ctx.message.channel.id)
        else:
            guild = '***'
            channel = 'direct message'

        user = str(ctx.message.author)
        userid = str(ctx.message.author.id)
        log.info('Inbox: %s/%s\n            %s (%s): %s', guild, channel, user, userid, arg)

    @commands.command(hidden=True)
    async def csay(self, ctx, dest, tts, *, msg):
        if ctx.message.author.id == 310618614497804289:
            if dest[0] == 'c':
                recip = self.bot.get_channel(dest[1:])
            elif dest[0] == 'd':
                recip = await self.bot.fetch_user(dest[1:])

            if tts == '1':
                tts = True
            else:
                tts = False

            await recip.send(msg, tts=tts)

    @commands.command()
    async def bigmoji(self, ctx, emoji):
        """Get larger version of either a default or custom emoji!"""

        path = imagetools.bigmoji(emoji)

        try:
            await ctx.send(file=discord.File(path, path))
        except Exception:
            await self.bot.say('*Not a valid emoji.*')

    @commands.command(brief='Get info on when to see the ISS from the location you search!')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def iss(self, ctx, *location):
        """
        Find out when the International Space Station will be visible to the naked eye from the location you search!
        Search any location (city, postal code, address, etc).
        The output is data from heavens-above.com that will tell you where in the sky to look and when (in local time).

        · Start: This is where the ISS becomes visible.
          It will take a minute or so longer for it to become visible
          because of the atomosphere and objects (such as trees) on the horizon.
        · Highest: This is its highest point in the pass. Note the elevation in parenthesis.
          For reference, 0° is the horizon and 90° is directly overhead.
        · End: This is where the ISS will pass out of view.
          In late evening passes, this happens well above the horizon.
          You just watched the ISS pass into the Earth's shadow!
        · Brightness: The magnitude is how bright the ISS is expected to be at your location.
          The lower the number, the brighter the ISS will appear. For example, -3.0 is brighter than 1.0!

        (Note: This command works in DM if you want to keep your location private.)
        """

        location = ' '.join(location).upper()
        lat, lon, passes, url = astronomy.get_iss_loc(location, 'ha')
        string_list = c.crimsplit(passes, '\n', limit=1600)
        for i in range(len(string_list)):
            header_string = 'Visible ISS passes (local time) for {} ({}°, {}°):\n'.format(location, lat, lon)
            header_string += 'Source: <{}>\n'.format(url)
            await ctx.send((header_string if i == 0 else '') + '```{}```'.format(string_list[i]))

    @commands.command(aliases=['map'])
    @commands.cooldown(3, 10, commands.BucketType.channel)
    async def location(self, ctx, *location):
        """Get a map of a location."""

        location = ' '.join(location).upper()
        map_url = astronomy.whereis(location)

        if map_url is not False:
            embed = c.crimbed('Map of {}\n{}'.format(location, map_url), None, None)
            embed.set_image(url=map_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send('*Location not found.*')


def setup(bot):
    bot.add_cog(Utilities(bot))

import logging
from typing import Optional

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import astronomy, image as imagetools, tools as c

log = logging.getLogger(__name__)


class Utilities(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot


    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def ping(self, ctx: commands.Context) -> None:
        """Need ping? 10s cooldown after use."""

        msg = await ctx.send('<:ping:569954524932997122>...')
        time_in = ctx.message.created_at
        time_out = msg.created_at
        ping = (time_out - time_in).microseconds / 1000
        await msg.edit(content='<:ping:569954524932997122>...{:d}ms'.format(int(ping)))


    @commands.command()
    async def color(self, ctx: commands.Context, hex_value: discord.Colour) -> None:
        """Get color sample from hex value."""

        fp = imagetools.make_color_img(str(hex_value))
        await ctx.send(
            '**' + str(hex_value) + '**',
            file=discord.File(fp, 'color.jpg')
        )


    @commands.command()
    @commands.cooldown(2, 8, commands.BucketType.guild)
    async def palette(self, ctx: commands.Context, number_of_colors: int, link: Optional[str] = None) -> None:
        """
        Get an image's main colors! Specify # of colors (1-10).
        • Must follow >palette with an integer between 1 and 10 then either an attached image or a link to an image.
        • Best results typically around 5 colors.
        • SVGs are no.
        • Images with transparency will sometimes produce a less-than-stellar palette.
        """

        if not 1 <= number_of_colors <= 10:
            raise commands.BadArgument('Number of colors is out of bounds.')

        hex_color, mosaic, resample = await imagetools.get_image_palette(ctx, number_of_colors, link)
        await ctx.send(
            '**Resampled image:**',
            file=discord.File(resample, 'resample.png')
        )
        await ctx.send(
            '**' + hex_color.upper() + '**',
            file=discord.File(mosaic, 'mosaic.png')
        )


    @commands.command(hidden=True)
    @commands.is_owner()
    async def csay(self, ctx: commands.Context, dest: str, tts: bool, *, message: str) -> None:
        if dest[0] == 'c':
            recip = self.bot.get_channel(int(dest[1:]))
        elif dest[0] == 'd':
            recip = await self.bot.fetch_user(int(dest[1:]))

        await recip.send(message, tts=tts)


    @commands.command()
    async def bigmoji(self, ctx: commands.Context, emoji: str) -> None:
        """Get larger version of either a default or custom emoji!"""

        path, emoji_type = imagetools.bigmoji(emoji)

        try:
            if emoji_type == 'file':
                await ctx.send(file=discord.File(path, path))
            elif emoji_type == 'url':
                await ctx.send(path)
        except Exception:
            await ctx.send('*Not a valid emoji.*')


    @commands.command(brief='Get info on when to see the ISS from the location you search!')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def iss(self, ctx: commands.Context, *, location: str) -> None:
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

        location = location.upper()
        lat, lon, passes, url = await astronomy.get_iss_loc(location, 'ha')
        string_list = c.crimsplit(passes, '\n', limit=1600)
        for i in range(len(string_list)):
            header_string = 'Visible ISS passes (local time) for {} ({}°, {}°):\n'.format(location, lat, lon)
            header_string += 'Source: <{}>\n'.format(url)
            await ctx.send((header_string if i == 0 else '') + '```{}```'.format(string_list[i]))


    @commands.command()
    @commands.cooldown(3, 10, commands.BucketType.channel)
    async def map(self, ctx: commands.Context, *, location: str) -> None:
        """Get a map of a location."""

        location = location.upper()
        lat, lon, map_url = astronomy.whereis(location)

        if map_url is not None:
            embed = c.crimbed(
                title='Map of {}\n{}'.format(location, map_url),
                descr=None,
                footer="{}°, {}°".format(lat, lon)
            )
            embed.set_image(url=map_url)
        else:
            embed = c.crimbed(
                title="**not good with location**",
                descr="Location **{}** not found.".format(location),
                thumb_name="weary",
                footer="pls to help"
            )
        await ctx.send(embed=embed)



def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Utilities(bot))

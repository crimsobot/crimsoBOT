import discord
from discord.ext import commands
from .clib import crimsotools as c
from .clib import imagetools as imagetools
from .clib import astronomy as astronomy


class Utilities:
    def __init__(self,bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.cooldown(1, 10, commands.BucketType.server)
    async def ping(self,ctx):
        """Need ping? 10s cooldown after use."""
        msg = await self.bot.say('<:ping:569954524932997122>...')
        timeIn = ctx.message.timestamp
        timeOut = msg.timestamp
        ping = (timeOut-timeIn).microseconds/1000
        await self.bot.edit_message(msg, '<:ping:569954524932997122>...{:d}ms'.format(int(ping)))

    @commands.command(pass_context=True)
    async def color(self, ctx, hex_value):
        """Get color sample from hex value."""
        imagetools.color(str(hex_value))
        await self.bot.send_file(ctx.message.channel,
                                 c.clib_path_join('img', 'color.jpg'),
                                 content='**'+hex_value+'**')

    @commands.command(pass_context=True,
        brief='Get an image\'s main colors! Specify # of colors (1-10).',
        description='• Must follow >palette with an integer between 1 and 10 '+
            'then either an attached image or a link to an image.\n• Best '+
            'esults typically around 5 colors.\n• SVGs are no.\n• Images with '+
            'transparency will sometimes produce a less-than-stellar palette.')
    @commands.cooldown(2, 8, commands.BucketType.server)
    async def palette(self, ctx, number_of_colors, link=None):
        """Get an image's main colors! Specify # of colors (1-10)."""
        print('----IN PROGRESS---- | palette running on {}/{}...'.format(ctx.message.server, ctx.message.channel))
        try:
            if not 1 <= int(number_of_colors) <= 10:
                raise ValueError
        except ValueError:
            return commands.CommandInvokeError(False)
        hex = imagetools.imagePalette(ctx, int(number_of_colors), link)
        await self.bot.send_file(ctx.message.channel,
                                 c.clib_path_join('img', 'resample.png'),
                                 content='**Resampled image:**')
        await self.bot.send_file(ctx.message.channel,
                                 c.clib_path_join('img', 'mosaic.png'),
                                 content='**'+hex.upper()+'**')
        c.botlog('palette COMPLETE on {}/{}!'.format(ctx.message.server, ctx.message.channel))

    @commands.command(pass_context=True, hidden=True)
    async def dearcrimso(self, ctx, *, arg):
        """Leave a message in crimso's inbox. Spam = ban"""
        if ctx.message.server is not None:
            server = str(ctx.message.server.name)
            channel = str(ctx.message.channel.id)
        else:
            server = '***'
            channel = 'direct message'
        user = str(ctx.message.author)
        userid = str(ctx.message.author.id)
        c.botlog(server+'/'+channel+'\n            '+ \
                 user+'('+userid+'): '+arg)

    @commands.command(pass_context=True, hidden=True)
    async def csay(self, ctx, dest, tts, *, msg):
        if ctx.message.author.id =='310618614497804289':
            if dest[0] == 'c':
                recip = self.bot.get_channel(dest[1:])
            elif dest[0] == 'd':
                recip = await self.bot.get_user_info(dest[1:])
            if tts == '1':
                tts = True
            else:
                tts = False
            await self.bot.send_message(recip, msg, tts=tts)

    @commands.command(pass_context=True)
    async def bigmoji(self, ctx, emoji):
        """Get larger version of either a default or custom emoji!"""
        path = imagetools.bigmoji(emoji)
        try:
            if path.startswith('http'):
                await self.bot.send_message(ctx.message.channel, path)
            else:
                await self.bot.send_file(ctx.message.channel, path)
        except:
            await self.bot.say('*Not a valid emoji.*')

    @commands.command(pass_context=True,
                      brief='Get info on when to see the ISS from the location you search!',
                      description='Find out when the International Space Station will be visible to the naked eye from the location you search! Search any location (city, postal code, address, etc). '+
                                  'The output is data from heavens-above.com that will tell you where in the sky to look and when (in local time).\n' +
                                  '· Start: This is where the ISS becomes visible. It will take a minute or so longer for it to become visible because of the atomosphere and objects (such as trees) on the horizon.\n'
                                  '· Highest: This is its highest point in the pass. Note the elevation in parenthesis. For reference, 0° is the horizon and 90° is directly overhead.\n'+
                                  '· End: This is where the ISS will pass out of view. In late evening passes, this happens well above the horizon. You just watched the ISS pass into the Earth\'s shadow!\n'+
                                  '· Brightness: The magnitude is how bright the ISS is expected to be at your location. The lower the number, the brighter the ISS will appear. For example, -3.0 is brighter than 1.0!\n\n'+
                                  '(Note: This command works in DM if you want to keep your location private.)')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def iss(self, ctx, *location):
        location = ' '.join(location).upper()
        lat, lon, passes, url = astronomy.ISS(location, 'ha')
        # string = '\n'.join(event for event in passes)
        string = passes
        await self.bot.say('Visible ISS passes (local time) for {} ({}°, {}°):\n'.format(location, lat, lon) + '```{}```'.format(string)+'Source: {}'.format(url))

    @commands.command(pass_context=True)
    @commands.cooldown(3, 10, commands.BucketType.channel)
    async def map(self, ctx, *location):
        """Get a map of a location."""
        location = ' '.join(location).upper()
        map_url = astronomy.whereis(location)
        if map_url is not False:
            embed = c.crimbed('Map of {}\n{}'.format(location, map_url), None, None)
            embed.set_image(url=map_url)
            await self.bot.send_message(ctx.message.channel, embed=embed)
        else:
            await self.bot.say('*Location not found.*')

def setup(bot):
    bot.add_cog(Utilities(bot))

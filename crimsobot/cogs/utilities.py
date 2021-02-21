import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.exceptions import LocationNotFound
from crimsobot.utils import astronomy, image as imagetools, tools as c

log = logging.getLogger(__name__)


class Utilities(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.command(aliases=['vote'], brief='Create a poll!')
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def poll(self, ctx: commands.Context, *, poll_input: str) -> None:
        """Make a poll! Use the form of some question;option 1;option 2;etc.
        For example:

        >poll What should I eat?;tacos;ramen;the rich

        Polls can have up to 20 choices, but keep in mind Discord's 2000-character message limit.
        Polls technically never close, but you can >tally the results whenever you like!
        """

        poll_pool = [
            '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟',
            '🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯'
        ]

        choices = poll_input.split(';')
        question = choices.pop(0).strip()

        # some tests to ensure there's a question and at least two choices
        if len(question) == 0:
            question = 'QUICK POLL!'

        # message attachment if it exists, and ward off unbound local var errors
        attachment = None

        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]

        choices = [choice.strip() for choice in choices if len(choice.strip()) != 0]

        if len(choices) < 2:
            return

        # poll embned
        poll_body = ['**{}**\n'.format(question)]
        for idx, choice in enumerate(choices):
            poll_body.append('{} {}'.format(poll_pool[idx], choice))

        embed = c.crimbed(
            title='{} has created a poll!'.format(ctx.author),
            descr='{}'.format('\n'.join(poll_body)),
            thumb_name='think',
            footer='\u200dPoll ID: {d.month}{d.day}{d.hour}{d.minute}{d.second}'.format(d=datetime.utcnow())
        )

        if attachment:
            embed.set_image(url=attachment.url)

        msg = await ctx.send(embed=embed)

        # add reactions to msg
        for emoji in poll_pool[0:len(choices)]:
            try:
                await msg.add_reaction(emoji)
                await asyncio.sleep(0.36)  # smoother rollout of reactions
            except Exception:
                await ctx.send('**Someone added emojis!** Wait for me to add them, then choose. `Poll crashed.`')
                return

    @commands.command(aliases=['tally', 'votetally'], brief='Tally results of a poll!')
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def polltally(self, ctx: commands.Context, poll_id: Optional[str] = None) -> None:
        """Tally the results of the most recent poll in a channel, or of a previous poll if you give the poll's ID.
        You can only tally the results of a poll in the same channel as the poll.
        Tallying a poll does not close the poll; its results can be tallied again if it's not too old."""

        # so this is kinda hacky...
        # first, check channel's message history (backwards from present) for prior polls from bot
        poll_found = False

        async for message in ctx.channel.history(limit=10000):
            if message.author.id == self.bot.user.id and len(message.embeds) != 0:
                # look for a footer; if no footer, TypeError is raised.
                try:
                    if '\u200dPoll ID:' not in message.embeds[0].footer.text:
                        continue
                except TypeError:
                    continue
                # grab poll ID from embed to check against user input, if any
                poll_id_from_embed = message.embeds[0].footer.text.replace('\u200dPoll ID: ', '')
                # if none supplied, then most recent poll it is; if not, check IDs against each other
                if poll_id is None or poll_id == poll_id_from_embed:
                    poll_found = True
                    descr = message.embeds[0].description
                    reactions = message.reactions
                    image_url = None
                    if message.embeds[0].image:
                        image_url = message.embeds[0].image.url  # this looks kind of yucky

                    url = message.jump_url
                    break

        if not poll_found:
            await ctx.send('`Poll ID not found, or poll is too old.`', delete_after=10)
            return

        # both the question and the choices will be in here; split into list
        descr = descr.split('\n')

        # find where the options begin; separate questions and options
        for idx, option in enumerate(descr):
            if '1️⃣' in option:
                options_begin = idx

        question = '\n'.join(descr[:options_begin])
        options = descr[options_begin:]

        # count reactions; they will be in order 1-10, A-J
        reaction_counts: List[Tuple[str, int]] = []
        for reaction in reactions:
            reaction_counts.append((reaction.emoji, reaction.count))

        # this becomes the description in the tally embed
        poll_body = ['{}'.format(question)]
        for idx, choice in enumerate(options):
            count = reaction_counts[idx][1] - 1
            ess = '' if count == 1 else 's'
            poll_body.append('{} · **{}** vote{}'.format(choice, count, ess))

        # create embed and send
        embed = c.crimbed(
            title='{} has tallied a poll!'.format(ctx.author),
            descr='{}'.format('\n'.join(poll_body)),
            thumb_name='think',
            footer='Tally as of {} UTC'.format(datetime.utcnow().strftime('%Y %b %d %H:%M:%S'))
        )

        if image_url:
            embed.set_thumbnail(url=image_url)

        embed.add_field(
            name='Poll ID: {}'.format(poll_id_from_embed),
            value='[Jump to poll]({})'.format(url),
            inline=False
        )

        await ctx.send(embed=embed)

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

        path, emoji_type = imagetools.find_emoji_img(emoji)

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
        lat, lon, url, passes = await astronomy.get_iss_loc(location)
        if not url:
            raise LocationNotFound(location)

        header_string = (
            f'Visible ISS passes (local time) for {location} ({lat}°, {lon}°):\n'
            f'Source: <{url}>\n'
        )

        formatted_passes = astronomy.format_passes(passes)

        string_list = c.crimsplit(formatted_passes, '\n', limit=1600)
        for i, string in enumerate(string_list):
            # if i is falsey it must be 0, which means we can send without the header string
            await ctx.send(f'```{string}```' if i else f'{header_string}```{string}```')

    @commands.command(name='map')
    @commands.cooldown(3, 10, commands.BucketType.channel)
    async def get_map(self, ctx: commands.Context, *, location: str) -> None:
        """Get a map of a location."""

        location = location.upper()
        lat, lon, map_url = astronomy.whereis(location)

        if map_url is not None:
            embed = c.crimbed(
                title='Map of {}\n{}'.format(location, map_url),
                descr=None,
                footer='{}°, {}°'.format(lat, lon)
            )
            embed.set_image(url=map_url)
        else:
            raise LocationNotFound(location)

        await ctx.send(embed=embed)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Utilities(bot))

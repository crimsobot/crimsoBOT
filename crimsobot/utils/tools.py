import asyncio
import functools
import logging
import os
import random
from typing import Any, Awaitable, Callable, List, Optional

from discord import ChannelType, Embed, Guild

log = logging.getLogger(__name__)


class ImageAlreadySet(Exception):
    def __init__(self, *args: Any):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self) -> str:
        if self.message:
            return 'ImageAlreadySet, {0} '.format(self.message)
        else:
            return 'ImageAlreadySet: cannot set two images for an embed'


def executor_function(sync_function: Callable) -> Callable:
    @functools.wraps(sync_function)
    async def sync_wrapper(*args: Any, **kwargs: Any) -> Awaitable[Any]:
        loop = asyncio.get_event_loop()
        reconstructed_function = functools.partial(sync_function, *args, **kwargs)
        return await loop.run_in_executor(None, reconstructed_function)

    return sync_wrapper


def crimbed(title: Optional[str], descr: Optional[str],
            thumb_name: Optional[str] = None, color_name: Optional[str] = 'green',
            image_url: Optional[str] = None, attachment: Optional[str] = None,
            footer: Optional[str] = None) -> Embed:
    """Discord embed builder with preset options for crimsoBOT colors and thumbnails."""

    color_dict = {
        'green': 0x5AC037,
        'yellow': 0xEEE23C,
        'orange': 0xE2853C,
    }

    if color_name == 'random':
        name, hex_int = random.choice(list(color_dict.items()))
    elif color_name is not None:
        hex_int = color_dict[color_name]
    else:
        hex_int = color_dict['green']

    embed = Embed(title=title, description=descr, color=hex_int)

    # Give these one-word names, no spaces.
    random_thumb_dict = {
        'triumph': 'https://i.imgur.com/bBXRFnO.png',
        'joy': 'https://i.imgur.com/8deo8Ak.png',
        'hug': 'https://i.imgur.com/lSPKbWf.png',
        # 'think': 'https://i.imgur.com/odD9yI2.png',
        'think': 'https://i.imgur.com/L6tdtKB.png',
        'scared': 'https://i.imgur.com/sppk4te.png',
        'weary': 'https://i.imgur.com/VFtApPg.png',
        'moneymouth': 'https://i.imgur.com/lNR8qHe.png',
        'shrug': 'https://i.imgur.com/CmokCt9.png',
        'nerd': 'https://i.imgur.com/IFqf0X7.png',
    }

    # These thumbnails are for specific uses only.
    specific_thumb_dict = {
        'jester': 'https://i.imgur.com/gpRToBn.png',  # Cringo!
        'crimsoCOIN': 'https://i.imgur.com/rS2ec5d.png',  # bal
        'pfp': 'https://i.imgur.com/9UTNIGi.png',
        'monty': 'https://i.imgur.com/wOFf7PF.jpg',
        '8ball': 'https://i.imgur.com/6dzqq78.png',
        'small': 'https://i.imgur.com/IrjA6zq.png',
        'clock': 'https://i.imgur.com/2eAdhsW.png',
        'wizard': 'https://i.imgur.com/anaCs7G.png',
    }

    if thumb_name:
        try:
            if thumb_name == 'random':
                name, url = random.choice(list(random_thumb_dict.items()))
            else:
                try:
                    url = specific_thumb_dict[thumb_name]
                except KeyError:
                    try:
                        url = random_thumb_dict[thumb_name]
                    except KeyError:
                        url = thumb_name
            embed.set_thumbnail(url=url)
        except KeyError:
            pass

    image_already_set = False

    if image_url is not None:
        embed.set_image(url=image_url)
        image_already_set = True

    if attachment is not None:
        if image_already_set is False:
            embed.set_image(url='attachment://{}'.format(attachment))
            image_already_set = True
        else:
            raise ImageAlreadySet

    if footer is not None:
        embed.set_footer(text=footer)

    return embed


def crimsplit(long_string: str, break_char: str, limit: int = 2000) -> List[str]:
    """Break a string."""

    list_of_strings = []
    while len(long_string) > limit:
        # find indexes of all break_chars; if no break_chars, index = limit
        index = [i for i, brk in enumerate(long_string) if brk == break_char]

        if index == [] or max(index) < limit:
            index.append(limit)

        # find first index at or past limit, break message
        for ii in range(0, len(index)):
            if index[ii] >= limit:
                list_of_strings.append(long_string[:index[ii - 1]].lstrip(' '))
                long_string = long_string[index[ii - 1]:]
                break  # back to top, if long_string still too long

    # include last remaining bit of long_string and return
    list_of_strings.append(long_string)

    return list_of_strings


def clib_path_join(*paths: str) -> str:
    utils_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(utils_path, '..', 'data', *paths)


def get_guild_info_embed(guild: Guild) -> Embed:
    # initialize embed
    embed = Embed(
        title=guild.name,
        description='**`{s}`** has `{m}` members, `{r}` roles and is owned by `{s.owner}`'.format(
            s=guild, m=len(guild.members), r=len(guild.roles)
        )
    )

    # number of channels to show, which to show
    channel_list = [x for x in sorted(guild.channels, key=lambda c: c.position) if x.type == ChannelType.text]
    show = min(10, len(guild.channels))
    channel_text = '\n'.join([('· {channel.name}'.format(channel=channel)) for channel in channel_list[:show]])
    embed.add_field(
        name='Channels ({}/{} shown)'.format(show, len(guild.channels)),
        value=channel_text or 'No channels.',
        inline=False
    )

    # number of roles to show, which to show
    role_list = [x for x in guild.roles if not x.is_default()]
    show = min(10, len(role_list))
    role_text = '\n'.join(['· {s}{name}'.format(s='@' if r.mentionable else '', name=r.name) for r in role_list[:show]])
    embed.add_field(
        name='Roles ({}/{} shown)'.format(show, len(guild.roles) - 1),  # minus 1 to not include @everyone
        value=role_text or 'No roles.',
        inline=False
    )

    # list emojis; truncate if need be
    show = len(guild.emojis)
    total = show
    char_count = sum([len(emoji.name) for emoji in guild.emojis])
    if char_count > 500:
        while char_count > 500:
            guild.emojis = guild.emojis[:-1]
            show = len(guild.emojis)
            char_count = sum([len(emoji.name) for emoji in guild.emojis])
    emoji_text = ' '.join(['`:{e.name}:`'.format(e=emoji) for emoji in guild.emojis[:show]])
    embed.add_field(
        name='Emojis ({}/{} shown)'.format(show, total),
        value=emoji_text or 'No custom emojis.',
        inline=False
    )

    # footer, thumbnail
    embed.set_footer(text='Server ID: #{guild.id}'.format(guild=guild))
    embed.set_thumbnail(url=guild.icon_url)

    return embed

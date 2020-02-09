import logging
import os
from typing import List, Optional, Union

from discord import ChannelType, DMChannel, Embed, GroupChannel, Guild, Member, TextChannel, User

log = logging.getLogger(__name__)

Messageables = Union[DMChannel, GroupChannel, Member, TextChannel, User]


def checkin(cmd: str, guild: Guild, channel: Messageables, running: List[int]) -> bool:
    """Is game already running in channel/DM?"""

    if channel.id in running:
        return False

    running.append(channel.id)

    if guild:
        guild_name = guild.name
    else:
        guild_name = '*'

    log.info('%s running on %s/%s (%s)...', cmd, guild_name, channel, channel.id)

    return True


def checkout(cmd: str, guild: Guild, channel: Messageables, running: List[int]) -> None:
    """Is game already running in channel/DM?"""

    running.remove(channel.id)

    if guild:
        guild_name = guild.name
    else:
        guild_name = '*'

    log.info('%s COMPLETE on %s/%s!', cmd, guild_name, channel)


def crimbed(title: Optional[str], description: Optional[str], thumbnail: Optional[str] = None,
            color: Optional[int] = 0x5AC037, footer: Optional[str] = None) -> Embed:
    embed = Embed(title=title, description=description, color=color)
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)
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

import datetime
import logging
import os
import pickle
import sys

from discord import ChannelType, Embed

log = logging.getLogger(__name__)

sys.modules['crimsotools'] = sys.modules[__name__]


class CrimsoBOTUser(object):
    def __init__(self, user_id):
        self.ID = user_id       # Discord snowflake
        self.banned = False     # Whether user is banned from using the bot
        self.coin = 0.0         # User's account balance

        self.daily = datetime.datetime(1969, 7, 20, 0, 0, 0)  # Last usage of >daily

        self.guess_plays = 0        # Number of plays of guessemoji
        self.guess_expected = 0.0   # Total of expected chances of winning
        self.guess_wins = 0         # Total number of wins
        self.guess_luck = 0.0       # Guessemoji luck index

    # Tech debt: ensure attributes previously not present in __init__ are now present
    # Avoids having to handle AttributeError everywhere
    @staticmethod
    def _ensure_attrs(state):
        # Fix legacy discord.py string IDs
        if isinstance(state['ID'], str):
            state['ID'] = int(state['ID'])

        state['banned'] = state.get('banned', False)
        state['coin'] = state.get('coin', 0.0)
        state['daily'] = state.get('daily', datetime.datetime(1969, 7, 20, 0, 0, 0))
        state['guess_plays'] = state.get('guess_plays', 0)
        state['guess_expected'] = state.get('guess_expected', 0.0)
        state['guess_wins'] = state.get('guess_wins', 0)
        state['guess_luck'] = state.get('guess_luck', 0.0)

    # pickle.dump
    def __getstate__(self):
        state = self.__dict__.copy()
        self._ensure_attrs(state)

        return state

    # pickle.load
    def __setstate__(self, state):
        self._ensure_attrs(state)
        self.__dict__.update(state)

    @staticmethod
    def get(user_id: int) -> 'CrimsoBOTUser':
        filename = clib_path_join('users', str(user_id) + '.pickle')

        # Unserialize from user file
        try:
            with open(filename, 'rb') as f:
                user = pickle.load(f)  # type: CrimsoBOTUser

        # User file doesn't exist, create it.
        except FileNotFoundError:
            user = CrimsoBOTUser(user_id)
            user.ID = user_id

        return user

    def save(self):
        filename = clib_path_join('users', str(self.ID) + '.pickle')

        # Serialize to user file
        with open(filename, 'wb') as f:
            pickle.dump(self, f)


def checkin(cmd, guild, channel, running):
    """Is game already running in channel/DM?"""

    if channel.id in running:
        return False

    running.append(channel.id)

    if guild:
        guild_name = guild.name
    else:
        guild_name = '*'

    log.info('%s running on %s/%s (%s)...', cmd, guild_name, channel, channel.id)


def checkout(cmd, guild, channel, running):
    """Is game already running in channel/DM?"""

    running.remove(channel.id)

    if guild:
        guild_name = guild.name
    else:
        guild_name = '*'

    log.info('%s COMPLETE on %s/%s!', cmd, guild_name, channel)


def crimbed(title, description, thumbnail=None, color=0x5AC037):
    embed = Embed(title=title, description=description, color=color)
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)

    return embed


def crimsplit(long_string, break_char, limit=2000):
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


def is_banned(discord_user_id):
    cb_user_object = CrimsoBOTUser.get(discord_user_id)
    return cb_user_object.banned


def who_is_banned():
    """ input: none
       output: sorted list of CrimsoBOTUser objects"""

    cb_user_object_list = []

    for user_id in get_stored_user_ids():
        cb_user_object_list.append(CrimsoBOTUser.get(user_id))

    return [u for u in cb_user_object_list if u.banned]


def get_stored_user_ids():
    """Get a list of users the bot has stored data for"""

    for f in os.listdir(clib_path_join('users')):
        if not f.startswith('.'):
            yield f[:-7]


def clib_path_join(*paths):
    utils_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(utils_path, '..', 'data', *paths)


def get_guild_info_embed(guild):
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

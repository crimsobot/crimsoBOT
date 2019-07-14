import collections
from typing import List, Tuple

from discord import Embed
from discord.ext import commands

from crimsobot.utils.tools import CrimsoBOTUser, crimbed, get_stored_user_ids

PLACES_PER_PAGE = 10

Leader = collections.namedtuple('Leader', ['user_id', 'value'])


class Leaderboard:
    def __init__(self) -> None:
        self._leaders = []  # type: List[Leader]

        self._embed = crimbed(None, None, 'https://i.imgur.com/rS2ec5d.png')
        self._embed_footer_extra = ''  # type: str

    def get_coin_leaders(self) -> None:
        self._set_embed_title('coin')

        users = self._get_users()
        users.sort(key=lambda u: u.coin, reverse=True)

        for user in users:
            leader = Leader(
                user_id=user.ID,
                value='\u20A2{u.coin:.2f}'.format(u=user)
            )

            if user.coin > 0:
                self._leaders.append(leader)

    def get_luck_leaders(self) -> None:
        self._set_embed_title('luck')
        self._embed_footer_extra = ' · Minimum 50 plays (will increase with time)'

        users = self._get_users()
        users.sort(key=lambda u: u.guess_luck, reverse=True)

        for user in users:
            leader = Leader(
                user_id=user.ID,
                value='{:.3f} ({} plays)'.format(user.guess_luck * 100, user.guess_plays)
            )

            if user.guess_plays >= 50:
                self._leaders.append(leader)

    def get_plays_leaders(self) -> None:
        self._set_embed_title('plays')

        users = self._get_users()
        users.sort(key=lambda u: u.guess_plays, reverse=True)

        for user in users:
            leader = Leader(
                user_id=user.ID,
                value=str(user.guess_plays)
            )

            if user.guess_plays > 0:
                self._leaders.append(leader)

    async def get_embed(self, ctx: commands.Context, page: int) -> Embed:
        start, end = self._get_places(page)
        leaders = self._leaders[start:end]

        # add attributes in place: discord user object, place
        if not leaders:
            self._embed.add_field(name="You've gone too far!",
                                  value="There aren't that many players yet!",
                                  inline=False)
            self._embed_footer_extra = ' does not exist.'
        else:
            for place, leader in enumerate(leaders):
                discord_user = await ctx.bot.fetch_user(leader.user_id)
                place = start + place + 1
                self._embed.add_field(name='{p}. **{u.name}#{u.discriminator}**'.format(p=place, u=discord_user),
                                      value=leader.value,
                                      inline=False)

        self._embed.set_footer(text='Page {}{}'.format(page, self._embed_footer_extra))

        return self._embed

    def _get_users(self) -> List[CrimsoBOTUser]:
        users = []
        for user_id in get_stored_user_ids():
            users.append(CrimsoBOTUser.get(user_id))

        return users

    def _get_places(self, page: int) -> Tuple[int, int]:
        place_shift = (page - 1) * PLACES_PER_PAGE

        return place_shift, place_shift + PLACES_PER_PAGE

    def _set_embed_title(self, stat: str) -> None:
        stat = stat.upper()
        self._embed.title = '<:crimsoCOIN_symbol:588492640559824896> crimsoCOIN leaderboard: **{}**'.format(stat)

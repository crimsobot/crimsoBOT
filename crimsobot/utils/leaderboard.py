import collections
from typing import List

from discord import Embed
from discord.ext import commands

from crimsobot.models.currency_account import CurrencyAccount
from crimsobot.models.guess_statistic import GuessStatistic
from crimsobot.utils.tools import crimbed

PLACES_PER_PAGE = 10

Leader = collections.namedtuple('Leader', ['user_id', 'value'])


class Leaderboard:
    def __init__(self, page: int) -> None:
        self._leaders = []  # type: List[Leader]

        self._embed = crimbed(None, None, 'https://i.imgur.com/rS2ec5d.png')
        self._embed_footer_extra = ''  # type: str

        self.page = page
        self._offset = (page - 1) * PLACES_PER_PAGE

    async def get_coin_leaders(self) -> None:
        self._set_embed_title('coin')

        accounts = await CurrencyAccount \
            .filter(balance__gt=0) \
            .order_by('-balance') \
            .limit(PLACES_PER_PAGE) \
            .offset(self._offset) \
            .prefetch_related('user')  # type: List[CurrencyAccount]

        for account in accounts:
            leader = Leader(
                user_id=account.user.discord_user_id,
                value='\u20A2{:.2f}'.format(account.get_balance())
            )
            self._leaders.append(leader)

    async def get_luck_leaders(self) -> None:
        min_plays = 100
        self._set_embed_title('luck')
        self._embed_footer_extra = ' · Minimum {} plays (will increase with time)'.format(min_plays)

        stats = await GuessStatistic \
            .filter(plays__gte=min_plays) \
            .prefetch_related('user')  # type: List[GuessStatistic]

        # luck_index is a computed property (not actually stored in the DB), so we have to sort here instead
        stats.sort(key=lambda s: s.luck_index, reverse=True)
        stats = stats[self._offset:self._offset + PLACES_PER_PAGE]

        for stat in stats:
            leader = Leader(
                user_id=stat.user.discord_user_id,
                value='{:.3f} ({} plays)'.format(stat.luck_index * 100, stat.plays)
            )
            self._leaders.append(leader)

    async def get_plays_leaders(self) -> None:
        self._set_embed_title('plays')

        stats = await GuessStatistic \
            .filter(plays__gt=0) \
            .order_by('-plays') \
            .limit(PLACES_PER_PAGE) \
            .offset(self._offset) \
            .prefetch_related('user')  # type: List[GuessStatistic]

        for stat in stats:
            leader = Leader(
                user_id=stat.user.discord_user_id,
                value=str(stat.plays)
            )
            self._leaders.append(leader)

    async def get_embed(self, ctx: commands.Context) -> Embed:
        leaders = self._leaders

        # add attributes in place: discord user object, place
        if not leaders:
            self._embed.add_field(name="You've gone too far!",
                                  value="There aren't that many players yet!",
                                  inline=False)
            self._embed_footer_extra = ' does not exist.'
        else:
            for place, leader in enumerate(leaders):
                discord_user = await ctx.bot.fetch_user(leader.user_id)
                place = self._offset + place + 1
                self._embed.add_field(name='{p}. **{u.name}#{u.discriminator}**'.format(p=place, u=discord_user),
                                      value=leader.value,
                                      inline=False)

        self._embed.set_footer(text='Page {}{}'.format(self.page, self._embed_footer_extra))

        return self._embed

    def _set_embed_title(self, stat: str) -> None:
        stat = stat.upper()
        self._embed.title = '<:crimsoCOIN_symbol:588492640559824896> crimsoCOIN leaderboard: **{}**'.format(stat)

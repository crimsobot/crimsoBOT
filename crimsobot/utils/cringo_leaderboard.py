import collections
from typing import List

from discord import Embed
from discord.ext import commands

from crimsobot.models.cringo_statistic import CringoStatistic
from crimsobot.utils.tools import crimbed

PLACES_PER_PAGE = 10

Leader = collections.namedtuple('Leader', ['user_id', 'value'])


class CringoLeaderboard:
    def __init__(self, page: int) -> None:
        self._leaders = []  # type: List[Leader]

        self._embed = crimbed(title=None, descr=None, thumb_name='jester')
        self._embed_footer_extra = ''  # type: str

        self.page = page
        self._offset = (page - 1) * PLACES_PER_PAGE

    async def get_coin_leaders(self) -> None:
        self._set_embed_title('coin')

        stats = await CringoStatistic \
            .filter(coin_won__gt=0) \
            .order_by('-coin_won') \
            .limit(PLACES_PER_PAGE) \
            .offset(self._offset) \
            .prefetch_related('user')  # type: List[CringoStatistic]

        for stat in stats:
            leader = Leader(
                user_id=stat.user.discord_user_id,
                value='\u20A2{:.2f}'.format(stat.coin_won)
            )
            self._leaders.append(leader)

    async def get_wins_leaders(self) -> None:
        self._set_embed_title('wins')

        stats = await CringoStatistic \
            .filter(wins__gt=0) \
            .order_by('-wins') \
            .limit(PLACES_PER_PAGE) \
            .offset(self._offset) \
            .prefetch_related('user')  # type: List[CringoStatistic]

        for stat in stats:
            leader = Leader(
                user_id=stat.user.discord_user_id,
                value='{} wins'.format(stat.wins)
            )
            self._leaders.append(leader)

    async def get_plays_leaders(self) -> None:
        self._set_embed_title('plays')

        stats = await CringoStatistic \
            .filter(plays__gt=0) \
            .order_by('-plays') \
            .limit(PLACES_PER_PAGE) \
            .offset(self._offset) \
            .prefetch_related('user')  # type: List[CringoStatistic]

        for stat in stats:
            leader = Leader(
                user_id=stat.user.discord_user_id,
                value='{} games'.format(stat.plays)
            )
            self._leaders.append(leader)

    async def get_score_leaders(self) -> None:
        self._set_embed_title('high score')

        stats = await CringoStatistic \
            .filter(high_score__gt=0) \
            .order_by('-high_score') \
            .limit(PLACES_PER_PAGE) \
            .offset(self._offset) \
            .prefetch_related('user')  # type: List[CringoStatistic]

        for stat in stats:
            leader = Leader(
                user_id=stat.user.discord_user_id,
                value='{} points'.format(stat.high_score)
            )
            self._leaders.append(leader)

    async def get_embed(self, ctx: commands.Context) -> Embed:
        leaders = self._leaders

        # add attributes in place: discord user object, place
        if not leaders:
            self._embed.add_field(
                name="You've gone too far!",
                value="There aren't that many players yet!",
                inline=False
            )
            self._embed_footer_extra = ' does not exist.'
        else:
            for place, leader in enumerate(leaders):
                discord_user = await ctx.bot.fetch_user(leader.user_id)
                place = self._offset + place + 1
                self._embed.add_field(
                    name='{}. **{}**'.format(place, str(discord_user)),
                    value=leader.value,
                    inline=False
                )

        self._embed.set_footer(text='Page {}{}'.format(self.page, self._embed_footer_extra))

        return self._embed

    def _set_embed_title(self, stat: str) -> None:
        self._embed.title = '<:cringo:690799257216876585> CRINGO! leaderboard: **{}**'.format(stat.upper())

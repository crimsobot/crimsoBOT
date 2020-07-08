import collections
from typing import List

from discord import Embed
from discord.ext import commands
from tortoise.functions import Count

from crimsobot.models.fun_fact import FunFact
from crimsobot.utils.tools import crimbed

PLACES_PER_PAGE = 10

Leader = collections.namedtuple('Leader', ['subject', 'value'])


class FactLeaderboard:
    def __init__(self, page: int) -> None:
        self._leaders = []  # type: List[Leader]

        self._embed = crimbed(title=None, descr=None, thumb_name='think')
        self._embed_footer_extra = ''  # type: str

        self.page = page
        self._offset = (page - 1) * PLACES_PER_PAGE

    async def get_subject_leaders(self, guild: int) -> None:
        self._set_embed_title('subjects')

        stats = await FunFact.all() \
            .filter(guild_id=guild) \
            .annotate(subject_count=Count('uid')) \
            .group_by('subject') \
            .order_by('-subject_count') \
            .limit(PLACES_PER_PAGE) \
            .offset(self._offset) \
            .values('subject', 'subject_count')  # type: List[dict]

        for stat in stats:
            ess = 's' if stat['subject_count'] > 1 else ''
            leader = Leader(
                subject=stat['subject'],
                value=f"{stat['subject_count']} fact{ess}"
            )
            self._leaders.append(leader)

    async def get_embed(self, ctx: commands.Context) -> Embed:
        leaders = self._leaders

        # add attributes in place: discord user object, place
        if not leaders:
            self._embed.add_field(
                name="You've gone too far!",
                value="There aren't that many subjects yet!",
                inline=False
            )
            self._embed_footer_extra = ' does not exist.'
        else:
            for place, leader in enumerate(leaders):
                place = self._offset + place + 1
                self._embed.add_field(
                    name='{}. **{}**'.format(place, leader.subject),
                    value=leader.value,
                    inline=False
                )

        self._embed.set_footer(text='Page {}{}'.format(self.page, self._embed_footer_extra))

        return self._embed

    def _set_embed_title(self, stat: str) -> None:
        self._embed.title = 'FACTS! leaderboard: **{}**'.format(stat.upper())

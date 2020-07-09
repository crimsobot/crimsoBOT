import collections
from typing import List

from discord import Embed, NotFound
from discord.ext import commands
from tortoise.functions import Count

from crimsobot.models.fun_fact import FunFact
from crimsobot.utils.tools import crimbed

PLACES_PER_PAGE = 10

Leader = collections.namedtuple('Leader', ['subject', 'value'])


class FactLeaderboard:
    def __init__(self, page: int) -> None:
        self._leaders = []  # type: List[Leader]

        self._embed = crimbed(title=None, descr=None, thumb_name='nerd')
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

                # placeholder if subject needs to be edited; cannot be replaced in tuple
                new_subject = None

                # turn '<@[userid]>' strings into usernames e.g. @username#1234
                if '<@' in leader.subject:
                    words = leader.subject.split(' ')
                    for idx, word in enumerate(words):
                        if '<@' in word:
                            try:
                                discord_user = await ctx.bot.fetch_user(int(word[2:-1]))
                                words[idx] = f'@{str(discord_user)}'
                            except ValueError:
                                pass  # if a fact contains string '<@' but is not a user, e.g. '<@not_an_integer>`
                            except NotFound:
                                pass  # user not found

                    new_subject = ' '.join(words)

                self._embed.add_field(
                    name='{}. **{}**'.format(place, new_subject if new_subject else leader.subject),
                    value=leader.value,
                    inline=False
                )

        self._embed.set_footer(text='Page {}{}'.format(self.page, self._embed_footer_extra))

        return self._embed

    def _set_embed_title(self, stat: str) -> None:
        self._embed.title = 'FACTS! leaderboard: **{}**'.format(stat.upper())

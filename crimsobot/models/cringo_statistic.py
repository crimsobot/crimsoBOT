from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser
from crimsobot.models.user import User


class CringoStatistic(Model):
    uuid = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='cringo_statistics', index=True)

    plays = fields.IntField(default=0)
    wins = fields.IntField(default=0)

    coin_won = fields.FloatField(default=0.0)

    high_score = fields.IntField(default=0)
    total_score = fields.IntField(default=0)

    matches = fields.IntField(default=0)  # expected per game: 14.4 (exact)
    lines = fields.IntField(default=0)  # expected per game: 6.34 (monte carlo)
    full_cards = fields.IntField(default=0)  # expected per game: 0.1296 (exact)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

    @property
    def mean_score(self) -> float:
        if not self.plays:
            return 0.0

        return float(self.total_score / self.plays)

    @property
    def cringo_luck_index(self) -> float:
        if not self.plays:
            return 0.0

        # the expected mean score is 2263 according to monte carlo sim (n = 2.16 million)
        return float(self.total_score / self.plays / 2263)

    @classmethod
    async def get_by_discord_user(cls, discord_user: DiscordUser) -> 'CringoStatistic':
        user = await User.get_by_discord_user(discord_user)
        stat, _ = await CringoStatistic.get_or_create(user=user)  # type: CringoStatistic, bool

        return stat

    class Meta:
        table = 'cringo_statistics'

from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser
from crimsobot.models.user import User


class CringoStatistic(Model):
    uuid = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='cringo_statistics', index=True)

    plays = fields.IntField(default=0)
    wins = fields.IntField(default=0)

    coin_won = fields.FloatField(default=0)

    high_score = fields.IntField(default=0)
    mean_score = fields.IntField(default=0)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

    @classmethod
    async def get_by_discord_user(cls, discord_user: DiscordUser) -> 'CringoStatistic':
        user = await User.get_by_discord_user(discord_user)
        stat, _ = await CringoStatistic.get_or_create(user=user)  # type: CringoStatistic, bool

        return stat

    class Meta:
        table = 'cringo_statistics'

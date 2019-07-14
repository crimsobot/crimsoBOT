from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser


class User(Model):
    uuid = fields.UUIDField(pk=True)
    discord_user_id = fields.BigIntField(unique=True, index=True)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

    @classmethod
    async def get_by_discord_user(cls, discord_user: DiscordUser) -> 'User':
        user, _ = await cls.get_or_create(discord_user_id=discord_user.id)  # type: User, bool

        return user

    class Meta:
        table = 'users'

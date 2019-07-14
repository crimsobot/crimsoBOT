from tortoise import fields
from tortoise.models import Model


class User(Model):
    uuid = fields.UUIDField(pk=True)
    discord_user_id = fields.BigIntField(unique=True, index=True)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

    class Meta:
        table = 'users'

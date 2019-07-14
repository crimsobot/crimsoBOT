from tortoise import fields
from tortoise.models import Model


class Ban(Model):
    uid = fields.IntField(pk=True)

    target = fields.ForeignKeyField('models.User', related_name='bans', index=True)
    issuer = fields.ForeignKeyField('models.User', related_name='bans_issued', index=True)

    reason = fields.CharField(max_length=255)
    active = fields.BooleanField(default=True)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

    removed_at = fields.DatetimeField(null=True)
    remover = fields.ForeignKeyField('models.User', related_name='bans_removed', null=True)

    class Meta:
        table = 'bans'

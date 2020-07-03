from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser
from crimsobot.models.user import User


class FunFacts(Model):
    uuid = fields.UUIDField(pk=True)
    created_by = fields.ForeignKeyField('models.User', related_name='fun_facts', index=True)

    subject = fields.CharField(max_length=255)
    funfact = fields.CharField(max_length=1800)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)

    @classmethod
    async def get_by_subject(cls, subject: str) -> 'FunFacts':
        fact = await FunFacts.get(subject=subject)  # type: FunFacts

        return fact

    @classmethod
    async def create_fact(cls, creator, subject: str, funfact: str) -> 'FunFacts':
        user = await User.get_by_discord_user(creator)
        fact = await FunFacts.create(created_by=user, subject=subject, funfact=funfact)

        return fact

    class Meta:
        table = 'fun_facts'

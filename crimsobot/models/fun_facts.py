import random
from typing import Any

from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser
from crimsobot.models.user import User


class NoFactsExist(Exception):
    def __init__(self, *args: Any):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self) -> str:
        if self.message:
            return 'NoFactsExist, {0} '.format(self.message)
        else:
            return 'There are no facts about this subject'


class FunFacts(Model):
    uuid = fields.IntField(pk=True)
    created_by = fields.ForeignKeyField('models.User', related_name='fun_facts', index=True)
    created_in = fields.BigIntField()

    subject = fields.CharField(max_length=255)
    funfact = fields.CharField(max_length=1800)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)

    @classmethod
    async def create_fact(cls, creator: DiscordUser, guild: int, subject: str, funfact: str) -> 'FunFacts':
        user = await User.get_by_discord_user(creator)
        fact = await FunFacts.create(
            created_by=user, subject=subject, created_in=guild, funfact=funfact)  # type: FunFacts

        return fact

    @classmethod
    async def get_by_id(cls, fact_id: int, guild: int, owner: bool) -> 'FunFacts':
        if owner:
            fact = await FunFacts.get(uuid=fact_id).prefetch_related('created_by')  # type: FunFacts
        else:
            fact = await FunFacts.get(uuid=fact_id, created_in=guild).prefetch_related('created_by')

        return fact

    @classmethod
    async def get_by_subject(cls, subject: str, guild: int) -> 'FunFacts':
        all_facts = await FunFacts.filter(subject=subject, created_in=guild).prefetch_related('created_by')

        try:
            fact = random.sample(all_facts, 1)[0]  # type: FunFacts
        except ValueError:
            raise NoFactsExist

        return fact

    @classmethod
    async def delete_by_id(cls, fact_id: int, guild: int, owner: bool) -> int:
        if owner:
            removed_int = await FunFacts.filter(uuid=fact_id).delete()  # type: int
        else:
            removed_int = await FunFacts.filter(uuid=fact_id, created_in=guild).delete()

        return removed_int

    @classmethod
    async def delete_by_subject(cls, subject: str, guild: int) -> int:
        removed_int = await FunFacts.filter(subject=subject, created_in=guild).delete()  # type: int

        return removed_int

    class Meta:
        table = 'fun_facts'

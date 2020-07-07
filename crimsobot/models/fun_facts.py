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


class FunFact(Model):
    uid = fields.IntField(pk=True)
    created_by = fields.ForeignKeyField('models.User', related_name='fun_facts', index=True)
    guild_id = fields.BigIntField(index=True)

    subject = fields.CharField(max_length=255)
    body = fields.CharField(max_length=1800)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)

    @classmethod
    async def create_fact(cls, creator: DiscordUser, guild: int, subject: str, body: str) -> 'FunFact':
        user = await User.get_by_discord_user(creator)
        fact = await FunFact.create(
            created_by=user, subject=subject, guild_id=guild, body=body)  # type: FunFact

        return fact

    @classmethod
    async def get_by_id(cls, fact_id: int, guild: int, owner: bool) -> 'FunFact':
        if owner:
            fact = await FunFact.get(uid=fact_id).prefetch_related('created_by')  # type: FunFact
        else:
            fact = await FunFact.get(uid=fact_id, guild_id=guild).prefetch_related('created_by')

        return fact

    @classmethod
    async def get_by_subject(cls, subject: str, guild: int) -> 'FunFact':
        all_facts = await FunFact.filter(subject=subject, guild_id=guild).prefetch_related('created_by')

        try:
            fact = random.sample(all_facts, 1)[0]  # type: FunFact
        except ValueError:
            raise NoFactsExist

        return fact

    @classmethod
    async def delete_by_id(cls, fact_id: int, guild: int, owner: bool) -> int:
        if owner:
            removed_int = await FunFact.filter(uid=fact_id).delete()  # type: int
        else:
            removed_int = await FunFact.filter(uid=fact_id, guild_id=guild).delete()

        return removed_int

    @classmethod
    async def delete_by_subject(cls, subject: str, guild: int) -> int:
        removed_int = await FunFact.filter(subject=subject, guild_id=guild).delete()  # type: int

        return removed_int

    class Meta:
        table = 'fun_facts'

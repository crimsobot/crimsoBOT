from typing import Any

from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser
from crimsobot.models.user import User


class WordleResults(Model):
    uuid = fields.UUIDField(pk=True)
    name = fields.TextField(default='wordle result')

    user = fields.ForeignKeyField('models.User', related_name='wordle_results', index=True)
    guesses = fields.IntField()  # guesses to solve word (0 for quit)
    word = fields.TextField()  # word guessed

    created_at = fields.DatetimeField(null=True, auto_now_add=True)

    @classmethod
    async def create_result(cls, discord_user: DiscordUser, guesses: int, word: str) -> None:
        user = await User.get_by_discord_user(discord_user)

        result = WordleResults(user=user, guesses=guesses, word=word)

        await result.save()

    @classmethod
    async def fetch_all_by_user(cls, discord_user: DiscordUser) -> Any:
        user = await User.get_by_discord_user(discord_user)
        stat = await WordleResults.filter(user=user)

        return stat

    class Meta:
        table = 'wordle_results'

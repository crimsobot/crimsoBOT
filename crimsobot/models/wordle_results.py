from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser
from crimsobot.models.user import User


class WordleResults(Model):
    uuid = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='wordle_results', index=True)

    guesses = fields.IntField(default=0)  # guesses to solve word (0 for quit)
    word = fields.TextField(default='crimso')  # word guessed

    created_at = fields.DatetimeField(null=True, auto_now_add=True)

    @classmethod
    async def create_result(cls, discord_user: DiscordUser) -> 'WordleResults':
        user = await User.get_by_discord_user(discord_user)
        stat, _ = await WordleResults.get_or_create(user=user)  # type: WordleResults, bool

        return stat

    class Meta:
        table = 'wordle_results'

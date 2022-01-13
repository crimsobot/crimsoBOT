from fractions import Fraction

from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser
from crimsobot.models.user import User


class GuessStatistic(Model):
    uuid = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='guess_statistics', index=True)

    plays = fields.IntField(default=0)
    wins = fields.IntField(default=0)

    expected_wins_numerator = fields.BigIntField(default=0)
    expected_wins_denominator = fields.BigIntField(default=1)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

    @property
    def expected_wins(self) -> Fraction:
        numerator = self.expected_wins_numerator  # type: int
        denominator = self.expected_wins_denominator  # type: int

        return Fraction(numerator, denominator)

    def add_to_expected_wins(self, number_of_emoji: int) -> None:
        frac = self.expected_wins + Fraction(1, number_of_emoji)  # type: Fraction

        self.expected_wins_numerator = frac.numerator
        self.expected_wins_denominator = frac.denominator

    @property
    def luck_index(self) -> float:
        if not self.expected_wins:
            return 0.0

        return float(self.wins / self.expected_wins)

    @classmethod
    async def get_by_discord_user(cls, discord_user: DiscordUser) -> 'GuessStatistic':
        user = await User.get_by_discord_user(discord_user)
        print(user)
        stat, _ = await GuessStatistic.get_or_create(user=user)  # type: GuessStatistic, bool

        return stat

    class Meta:
        table = 'guess_statistics'

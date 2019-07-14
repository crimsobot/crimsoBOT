from tortoise import fields
from tortoise.models import Model

from crimsobot.models import DiscordUser
from crimsobot.models.user import User


class CurrencyAccount(Model):
    uuid = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='currency_accounts', index=True)

    balance = fields.IntField(default=0)
    ran_daily_at = fields.DatetimeField(null=True)

    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)

    def get_balance(self) -> float:
        bal = self.balance  # type: int

        return bal / 100.0

    def add_to_balance(self, amount: float) -> None:
        bal = self.balance  # type: int
        bal += int(amount * 100)
        self.balance = bal

    @classmethod
    async def get_by_discord_user(cls, discord_user: DiscordUser) -> 'CurrencyAccount':
        user = await User.get_by_discord_user(discord_user)
        account, _ = await CurrencyAccount.get_or_create(user=user)  # type: CurrencyAccount, bool

        return account

    class Meta:
        table = 'currency_accounts'

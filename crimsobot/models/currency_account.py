from tortoise import fields
from tortoise.models import Model


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

    class Meta:
        table = 'currency_accounts'

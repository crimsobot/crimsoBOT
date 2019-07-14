from tortoise import Tortoise

from config import DATABASE_URL


async def connect() -> None:
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': [
            'crimsobot.models.user',
            'crimsobot.models.ban',
            'crimsobot.models.currency_account',
            'crimsobot.models.guess_statistic'
        ]}
    )


async def create_schemas(safe: bool = True) -> None:
    await Tortoise.generate_schemas(safe=safe)


async def close() -> None:
    await Tortoise.close_connections()

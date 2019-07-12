from discord.ext import commands

from config import ADMIN_USER_IDS


class NotAdmin(commands.CheckFailure):
    pass


# TODO: Figure out how to type hint the return type of this decorator
def is_admin():  # type: ignore
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.id not in ADMIN_USER_IDS:
            raise NotAdmin('You are not an admin of this bot.')
        return True

    return commands.check(predicate)

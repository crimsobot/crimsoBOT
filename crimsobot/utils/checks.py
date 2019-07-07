from discord.ext import commands

from config import ADMIN_USER_IDS


class NotAdmin(commands.CheckFailure):
    pass


def is_admin():
    async def predicate(ctx: commands.Context):
        if ctx.author.id not in ADMIN_USER_IDS:
            raise NotAdmin('You are not an admin of this bot.')
        return True

    return commands.check(predicate)

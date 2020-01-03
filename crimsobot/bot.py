import asyncio
import logging
import random
from typing import Any, List, Union

import discord
from discord.ext import commands

from config import ADMIN_USER_IDS, BANNED_GUILD_IDS, DM_LOG_CHANNEL_ID, LEARNER_CHANNEL_IDS, LEARNER_USER_IDS
from crimsobot import db
from crimsobot.models.ban import Ban
from crimsobot.utils import checks, markov as m, tools as c


class CrimsoBOT(commands.Bot):
    def __init__(self, **kwargs: Any) -> None:
        command_prefix = '>'

        super().__init__(command_prefix, **kwargs)

        self.banned_user_ids = []  # type: List[int]

        self.log = logging.getLogger(__name__)
        self._extensions_to_load = [
            'crimsobot.extensions.presence',  # 'crimsobot.extensions.reminder',
            'crimsobot.cogs.admin', 'crimsobot.cogs.chat', 'crimsobot.cogs.games', 'crimsobot.cogs.image',
            'crimsobot.cogs.mystery', 'crimsobot.cogs.text', 'crimsobot.cogs.utilities'
        ]

    def load_extensions(self) -> None:
        for name in self._extensions_to_load:
            try:
                self.load_extension(name)
            except Exception as error:
                self.log.error('%s cannot be loaded: %s', name, error)

    def reload_extensions(self) -> None:
        for name in self._extensions_to_load:
            try:
                self.reload_extension(name)
            except Exception as error:
                self.log.error('%s cannot be reloaded: %s', name, error)

    async def start(self, *args: Any, **kwargs: Any) -> None:
        await db.connect()

        banned_user_ids = await Ban.filter(active=True).values_list(
            'target__discord_user_id',
            flat=True
        )  # type: List[int]
        self.banned_user_ids = banned_user_ids

        await super().start(*args, **kwargs)

    async def close(self) -> None:
        await super().close()
        await db.close()

    def is_banned(self, discord_user: Union[discord.User, discord.Member]) -> bool:
        return discord_user.id in self.banned_user_ids

    async def on_ready(self) -> None:
        self.log.info('crimsoBOT is online')

    async def on_resumed(self) -> None:
        self.log.warning('crimsoBOT RECONNECT')

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """
        Displays error messages to user for cooldown and CommandNotFound,
        and suppresses verbose error text for both in the console.
        """

        if isinstance(error, commands.CommandOnCooldown):
            self.log.error('Cooldown: %s // %s: %s', ctx.author, ctx.message.content, error)

            await ctx.send('**eat glass.** %.0fs cooldown.' % error.retry_after, delete_after=7)

        elif isinstance(error, commands.CommandInvokeError):
            self.log.error('Invoke: %s // %s: %s', ctx.author, ctx.message.content, error, exc_info=error)

            try:
                await ctx.send(':poop: `E R R O R` :poop:', delete_after=7)

            except discord.errors.Forbidden:
                self.log.error('Forbidden: %s // %s: %s', ctx.guild, ctx.channel.id, error)
        elif isinstance(error, commands.MissingRequiredArgument):
            self.log.error('MissingArgument: %s // %s: %s', ctx.author, ctx.message.content, error)

            await ctx.send('*this command requires more arguments. try `>help [cmd]`*', delete_after=7)

        elif isinstance(error, commands.BadArgument):
            self.log.error('BadArgument: %s // %s: %s', ctx.author, ctx.message.content, error)

            await ctx.send("*that's not a valid argument value! try `>help [cmd]`*", delete_after=7)

        elif isinstance(error, checks.NotAdmin):
            self.log.error('NotAdmin: %s // %s: %s', ctx.author, ctx.message.content, error)

            await ctx.send(':rotating_light: not crimso! :rotating_light:', delete_after=7)

        elif isinstance(error, commands.CommandNotFound):
            self.log.error(
                'NotFound/Forbidden: %s/%s // %s: %s',
                ctx.message.guild.id, ctx.message.channel, ctx.message.content, error
            )
        else:
            self.log.error('Uncaught exception', exc_info=error)

    async def on_message(self, message: discord.Message) -> None:
        if self.is_banned(message.author):
            return

        # DM self.logger
        is_dm = isinstance(message.channel, discord.DMChannel)
        if is_dm and message.author.id != self.user.id and not message.content.startswith('>'):  # crimsoBOT
            try:
                link = message.attachments[0].url
            except IndexError:
                link = ''

            dms_channel = self.get_channel(DM_LOG_CHANNEL_ID)
            await dms_channel.send(
                '`{} ({}):`\n{} {}'.format(message.channel, message.channel.id, message.content, link)
            )

        # process commands
        await self.process_commands(message)

        # learn from crimso
        if message.author.id in LEARNER_USER_IDS and message.channel.id in LEARNER_CHANNEL_IDS:
            m.learner(message.content)

        # respond to ping
        if self.user in message.mentions:
            await message.channel.send(m.crimso())

        # random chat
        if random.random() < 0.001 and not is_dm:
            await message.channel.send(m.crimso())

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Notify me when added to guild"""

        if guild.id in BANNED_GUILD_IDS:
            await guild.leave()
            self.log.warning('Banned guild %s attempted to add crimsoBOT.', guild.id)
            return

        self.log.info("Joined %s's %s [%s]", guild.owner, guild, guild.id)

        embed = c.get_guild_info_embed(guild)

        # ...and send
        for user_id in ADMIN_USER_IDS:
            user = await self.get_user(user_id)
            try:
                await user.send('Added to {guild}'.format(guild=guild), embed=embed)
            except Exception:
                await user.send('Added to {guild}'.format(guild=guild))

    def add_command(self, command):
        command.cooldown_after_parsing = True
        return super().add_command(command)                

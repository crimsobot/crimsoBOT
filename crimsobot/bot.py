import logging
from typing import Any, List, Union

import discord
from discord.ext import commands

from config import ADMIN_USER_IDS, BANNED_GUILD_IDS, DM_LOG_CHANNEL_ID, LEARNER_CHANNEL_IDS, LEARNER_USER_IDS
from crimsobot import db
from crimsobot.models.ban import Ban
from crimsobot.utils import markov as m, tools as c


class CrimsoBOT(commands.Bot):
    def __init__(self, **kwargs: Any) -> None:
        command_prefix = '>'
        owner_ids = set(ADMIN_USER_IDS)
        super().__init__(command_prefix, owner_ids=owner_ids, **kwargs)

        self.banned_user_ids = []  # type: List[int]

        self.log = logging.getLogger(__name__)
        self._extensions_to_load = [
            'crimsobot.extensions.presence',  # 'crimsobot.extensions.reminder',
            'crimsobot.cogs.admin',
            'crimsobot.cogs.chat',
            'crimsobot.cogs.cringo',
            'crimsobot.cogs.games',
            'crimsobot.cogs.image',
            'crimsobot.cogs.mystery',
            'crimsobot.cogs.text',
            'crimsobot.cogs.utilities',
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
        """For known exceptions, displays error message to user and suppresses verbose traceback in console."""

        traceback_needed = False

        if isinstance(error, commands.MaxConcurrencyReached):
            error_type = 'MAX CONCURRENCY'
            msg_to_user = '`Already running in this channel!`'

        elif isinstance(error, commands.CommandOnCooldown):
            error_type = 'COOLDOWN'
            msg_to_user = f'**eat glass!** {error.retry_after:.0f}s cooldown.'

        elif isinstance(error, commands.CommandInvokeError):
            error_type = 'INVOKE ERROR'
            traceback_needed = True
            msg_to_user = ':poop: `E R R O R` :poop:'

        elif isinstance(error, commands.MissingRequiredArgument):
            error_type = 'MISSING ARGUMENT'
            msg_to_user = f'This command requires more arguments. Try `>help {ctx.command.qualified_name}`'

        elif isinstance(error, commands.BadArgument):
            error_type = 'BAD ARGUMENT'
            msg_to_user = f"That's not a valid argument value! Try `>help {ctx.command.qualified_name}`"

        elif isinstance(error, commands.NotOwner):
            error_type = 'NOT OWNER'
            msg_to_user = ':rotating_light: not crimso! :rotating_light:'

        elif isinstance(error, commands.CommandNotFound):
            error_type = 'NOT FOUND'

        else:
            error_type = 'UNCAUGHT EXCEPTION'
            traceback_needed = True

        # send error message
        try:
            embed = c.crimbed(
                title=f'**{error_type}**!',
                descr=msg_to_user,
                thumb_name='weary',
                color_name='orange',
                footer='bad at computer. bad at computer!',
            )
            await ctx.send(embed=embed, delete_after=10)
        except discord.errors.Forbidden:
            error_type = 'FORBIDDEN'
            traceback_needed = True
        except UnboundLocalError:  # if no msg_to_user is given
            pass

        # log error
        try:
            guild_string = f'guild: {ctx.guild} ({ctx.guild.id})'
        except AttributeError:
            guild_string = 'guild: None (direct message)'

        self.log.error(
            '\n    '.join([
                error_type,
                guild_string,
                f' user: {ctx.author} ({ctx.author.id})',
                f'  msg: {ctx.message.content}\n',
            ]), exc_info=(error if traceback_needed else None)
        )

    async def on_message(self, message: discord.Message) -> None:
        # do not respond if message from banned user or a bot
        if self.is_banned(message.author) or message.author.bot:
            return

        # send DMs to the bot that are not bot commands to the specified channel
        is_dm = isinstance(message.channel, discord.DMChannel)
        if is_dm and not message.content.startswith(('>', '.')):
            try:
                link = message.attachments[0].url
            except IndexError:
                link = ''

            dms_channel = self.get_channel(DM_LOG_CHANNEL_ID)
            await dms_channel.send(
                '\n'.join([
                    f'`{message.channel}`',  # e.g. 'Direct message with username#1234'
                    f'`uid:{message.author.id}`',
                    f'`cid:{message.channel.id}`',
                    f'{message.content} {link}',
                ])
            )

        # process commands
        await self.process_commands(message)

        # learn from crimso
        if message.author.id in LEARNER_USER_IDS and message.channel.id in LEARNER_CHANNEL_IDS:
            m.learner(message.content)

        # this little piggy cleans pings from crimsonic messages
        cleaner = commands.clean_content(use_nicknames=False)

        # respond to ping with a Markov chain from crimso corpus
        if self.user in message.mentions:
            await message.channel.trigger_typing()
            crimsonic = await m.async_wrap(self, m.crimso)

            # no more pings!
            try:
                ctx = await self.get_context(message)
                cleaned_output = await cleaner.convert(ctx, crimsonic)
            except commands.errors.BadArgument:
                cleaned_output = crimsonic

            await message.channel.send(cleaned_output)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Notify me when added to guild"""

        if guild.id in BANNED_GUILD_IDS:
            self.log.warning(f'Banned guild {guild.id} attempted to add crimsoBOT.')
            await guild.leave()
            return

        self.log.info(f"Joined {guild.owner}'s {guild} ({guild.id})")

        embed = c.get_guild_info_embed(guild)

        # ...and send
        for user_id in ADMIN_USER_IDS:
            user = self.get_user(user_id)

            try:
                await user.send("I've been added to a server!", embed=embed)
            except Exception:
                await user.send(f"I've been added to {guild} ({guild.id})!")

    def add_command(self, command: commands.Command) -> None:
        command.cooldown_after_parsing = True

        super().add_command(command)

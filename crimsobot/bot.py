import logging
from typing import Any, List, Union

import discord
from discord.ext import commands
from discord.ext.commands import Paginator

from config import ADMIN_USER_IDS, BANNED_GUILD_IDS, DM_LOG_CHANNEL_ID, LEARNER_CHANNEL_IDS, LEARNER_USER_IDS
from crimsobot import db
from crimsobot.context import CrimsoContext
from crimsobot.data.img import CAPTION_RULES, IMAGE_RULES
from crimsobot.exceptions import (BadCaption, LocationNotFound, NoImageFound, NoMatchingTarotCard,
                                  NotDirectMessage, StrictInputFailed)
from crimsobot.help_command import PaginatedHelpCommand
from crimsobot.models.ban import Ban
from crimsobot.utils import markov as m, tools as c


class CrimsoBOT(commands.Bot):
    def __init__(self, **kwargs: Any) -> None:
        command_prefix = '>'
        owner_ids = kwargs.pop('owner_ids', set(ADMIN_USER_IDS))
        case_insensitive = kwargs.pop('case_insensitive', True)

        default_intents = discord.Intents(
            members=True,  # privileged intent, enable Members in dashbaord
            guilds=True,
            emojis=True,  # for guild emoji cache, used in get_guild_info_embed
            messages=True,
            reactions=True,
        )

        intents = kwargs.pop('intents', default_intents)

        paginator = Paginator(max_size=1336)
        help_command = PaginatedHelpCommand(paginator=paginator)
        help_command = kwargs.pop('help_command', help_command)

        super().__init__(
            command_prefix,
            owner_ids=owner_ids,
            case_insensitive=case_insensitive,
            intents=intents,
            help_command=help_command,
            **kwargs
        )

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
            'crimsobot.cogs.reactions',
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
        self.markov_cache = await m.initialize_markov()

        m.update_models.start(self)
        await super().start(*args, **kwargs)

    async def close(self) -> None:
        await super().close()
        await db.close()

        if m.update_models.is_running():
            m.update_models.cancel()

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

            if isinstance(error.original, NoMatchingTarotCard):
                error_type = 'CARD NOT FOUND'
                traceback_needed = False
                msg_to_user = "It seems like that tarot card doesn't exist! How curious..."

            if isinstance(error.original, NotDirectMessage):
                error_type = 'SLIDE INTO MY DMS'
                traceback_needed = False
                msg_to_user = 'This command can only be used in a direct message with the bot.'

            if isinstance(error.original, StrictInputFailed):
                error_type = '**OOPSIE**'
                traceback_needed = False
                msg_to_user = '\n'.join([
                    'Alright, so either:',
                    '· that emoji is not in this server,',
                    '· after cleaning up your input, there are no characters left, or',
                    '· your input is too long. (Under 10 characters pls!)',
                    '',
                    'Some Discord objects such as mentions have hidden characters that will make the input too long.'
                ])

            if isinstance(error.original, LocationNotFound):
                error_type = '**not good with location**'
                traceback_needed = False
                msg_to_user = f'Location **{error.original.location}** not found.'

            if isinstance(error.original, NoImageFound):
                error_type = '**NO IMAGE**'
                traceback_needed = False
                msg_to_user = f'Image must be in a reply or in {IMAGE_RULES["msg_scrape_limit"]} most recent messages.'

            if isinstance(error.original, BadCaption):
                error_type = '**BAD CAPTION**'
                traceback_needed = False
                msg_to_user = f'Caption most be between 1-{CAPTION_RULES["max_len"]} alphanumeric characters.'

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
            # too many of these make it to logs, and it's never useful info
            return

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

        # send DMs to the bot (that are not bot commands) to the specified channel
        is_dm = message.channel.type == discord.ChannelType.private
        if is_dm and not message.content.startswith(('>', '.')):
            # grab any attachments in message to send as links
            links = []
            for attachment in message.attachments:
                links.append(attachment.url)

            dms_channel = self.get_channel(DM_LOG_CHANNEL_ID)
            await dms_channel.send(
                '\n'.join([
                    f'`{message.channel}`',  # e.g. 'Direct message with username#1234'
                    f'`uid:{message.author.id}`',
                    f'`cid:{message.channel.id}`',
                    f'{message.content} {" ".join(links)}',
                ])
            )

        # Get context from message for command invocation and text generation
        ctx = await self.get_context(message, cls=CrimsoContext)

        # Only invoke commands if we can send messages. We can always send messages in DMs.
        can_invoke = ctx.guild.me.permissions_in(ctx.channel).send_messages if ctx.guild else True
        if can_invoke:
            await self.invoke(ctx)

        # learn from crimso
        if message.author.id in LEARNER_USER_IDS and message.channel.id in LEARNER_CHANNEL_IDS:
            m.learner(message.content)
            self.markov_cache['crimso'].stale = True  # Model has been updated - we should regenerate it

        # respond to ping with a Markov chain from crimso corpus
        if self.user in message.mentions:
            await message.channel.trigger_typing()
            crimsonic = await m.crimso(ctx)
            # This allows us to keep pings in messages and have them persist visually, but not actually ping any of the
            # affected members. Think of it as better mention scrubbing.
            no_pings = discord.AllowedMentions(everyone=False, users=False, roles=False)
            await message.channel.send(crimsonic, allowed_mentions=no_pings)

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

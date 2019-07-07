import asyncio
import logging
import random

import discord
from discord.ext import commands

import crimsobot.utils.markov as m
import crimsobot.utils.tools as c
from config import ADMIN_USER_IDS, BANNED_GUILD_IDS, DM_LOG_CHANNEL_ID, LEARNER_CHANNEL_IDS, LEARNER_USER_IDS, \
    LOG_LEVEL, REMINDER_CHANNEL_IDS, TOKEN


logging.basicConfig(
    format='[%(asctime)s] %(levelname)8s: %(message)s\t(%(name)s)',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=LOG_LEVEL
)
log = logging.getLogger(__name__)


bot = commands.Bot(command_prefix='>')


@bot.event
async def on_ready():
    log.info('crimsoBOT is online')


@bot.event
async def on_resumed():
    log.warning('crimsoBOT RECONNECT')


@bot.event
async def on_command_error(ctx, error):
    """
    Displays error messages to user for cooldown and CommandNotFound,
    and suppresses verbose error text for both in the console.
    """

    if isinstance(error, commands.errors.CommandOnCooldown):
        log.error('Cooldown: %s // %s: %s', ctx.message.author, ctx.message.content, error)

        msg = await ctx.send('**eat glass.** %.0fs cooldown.' % error.retry_after)
        await asyncio.sleep(7)
        await msg.delete()
    elif isinstance(error, commands.errors.CommandInvokeError):
        try:
            log.exception('Invoke: %s // %s: %s', ctx.message.author, ctx.message.content, error)

            msg = await ctx.send(':poop: `E R R O R` :poop:')
            await asyncio.sleep(7)
            await msg.delete()
        except discord.errors.Forbidden:
            log.error('Forbidden: %s // %s: %s', ctx.message.guild, ctx.message.channel.id, error)
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        log.error('Argument: %s // %s: %s', ctx.message.author, ctx.message.content, error)

        msg = await ctx.send('*this command requires more arguments. try `>help [cmd]`*')
        await asyncio.sleep(7)
        await msg.delete()
    elif isinstance(error, commands.errors.CommandNotFound):
        log.error(
            'NotFound/Forbidden: %s/%s // %s: %s',
            ctx.message.guild.id, ctx.message.channel, ctx.message.content, error
        )
    else:
        raise error


def reorder(string_in):
    """Reorders a string. Called iteratively to give scrolling effect."""

    string_out = string_in[1:] + string_in[0]
    return string_out


async def change_status():
    """Slow scrolling effect for "Playing" status message."""

    await bot.wait_until_ready()

    # status to scroll (about 25 characters recommended)
    current_status = 'crimsoBOT is watching...'
    while not bot.is_closed():
        current_status = reorder(current_status)
        await bot.change_presence(activity=discord.Game(current_status))
        await asyncio.sleep(7)


async def reminder():
    """"Sends a disappearing random reminder in default channel."""

    await bot.wait_until_ready()

    # open reminder text file, strip newlines at end
    reminder_list = open(c.clib_path_join('text', 'reminders.txt'),
                         encoding='utf-8', errors='ignore').readlines()
    reminder_list = [line[:-1] for line in reminder_list]
    reminder_list = [line.replace('\\n', '\n') for line in reminder_list]

    # send in current channel on startup, and then...
    while not bot.is_closed:
        # calc time to next msg
        time_until = int(random.gauss(900, 90))
        await asyncio.sleep(time_until)

        # then send to each channel in list
        for channel_id in REMINDER_CHANNEL_IDS:
            channel = bot.get_channel(channel_id)
            msg = await channel.send(random.choice(reminder_list))

            # delete after 10s if no reaction
            await asyncio.sleep(10)
            cache_msg = discord.utils.get(bot.cached_messages, id=msg.id)
            if not cache_msg.reactions:
                await msg.delete()


@bot.event
async def on_message(message):
    if c.is_banned(message.author.id):
        return

    # DM logger
    is_dm = isinstance(message.channel, discord.DMChannel)
    if is_dm and message.author.id != bot.user.id and not message.content.startswith('>'):  # crimsoBOT
        try:
            link = message.attachments[0].url
        except Exception:
            link = ''

        dms_channel = bot.get_channel(DM_LOG_CHANNEL_ID)
        await dms_channel.send(
            '`{} ({}):`\n{} {}'.format(message.channel, message.channel.id, message.content, link)
        )

    # process commands
    await bot.process_commands(message)

    # learn from crimso
    if message.author.id in LEARNER_USER_IDS and message.channel.id in LEARNER_CHANNEL_IDS:
        m.learner(message.content)

    # respond to ping
    if bot.user in message.mentions:
        await message.channel.send(m.crimso())

    # random chat
    if random.random() < 0.001 and not is_dm:
        await message.channel.send(m.crimso())


@bot.event
async def on_guild_join(guild):
    """Notify me when added to guild"""

    if guild.id in BANNED_GUILD_IDS:
        await guild.leave()
        log.warning('Banned guild %s attempted to add crimsoBOT.', guild.id)
        return

    log.info("Joined %s's %s [%s]", guild.owner, guild, guild.id)

    embed = c.get_guild_info_embed(guild)

    # ...and send
    for user_id in ADMIN_USER_IDS:
        user = await bot.get_user(user_id)
        try:
            await user.send('Added to {guild}'.format(guild=guild), embed=embed)
        except Exception:
            await user.send('Added to {guild}'.format(guild=guild))


# load cogs (modules)
if __name__ == '__main__':
    # create task for loop change_status
    bot.loop.create_task(change_status())

    # create task for reminder
    # bot.loop.create_task(reminder())

    # load in extensions/cogs
    extensions = ['admin', 'chat', 'games', 'image', 'mystery', 'text', 'utilities']
    for extension in extensions:
        try:
            bot.load_extension('crimsobot.cogs.{}'.format(extension))
        except Exception as error:
            log.error('%s cannot be loaded: %s', extension, error)

    bot.run(TOKEN)

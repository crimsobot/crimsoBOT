import asyncio
import os
import random

import discord
from discord.ext import commands

import crimsobot.utils.markov as m
import crimsobot.utils.tools as c
from config import TOKEN

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

bot = commands.Bot(command_prefix='>')

# names of cogs to load
extensions = ['admin', 'chat', 'games', 'image', 'mystery', 'text', 'utilities']


@bot.event
async def on_ready():
    print('\n')
    c.botlog('crimsoBOT is online')


@bot.event
async def on_resumed():
    c.botlog('crimsoBOT RECONNECT')


@bot.event
async def on_command_error(error, ctx):
    """
    Displays error messages to user for cooldown and CommandNotFound,
    and suppresses verbose error text for both in the console.
    """

    if isinstance(error, commands.errors.CommandOnCooldown):
        c.botlog('Cooldown: %s // %s: %s' % (ctx.message.author, ctx.message.content, error))

        msg = await bot.send_message(ctx.message.channel, content='**eat glass.** %.0fs cooldown.' % error.retry_after)
        await asyncio.sleep(7)
        await bot.delete_message(msg)
    elif isinstance(error, commands.errors.CommandInvokeError):
        try:
            c.botlog('Invoke: %s // %s: %s' % (ctx.message.author, ctx.message.content, error))

            msg = await bot.send_message(ctx.message.channel, content=':poop: `E R R O R` :poop:')
            await asyncio.sleep(7)
            await bot.delete_message(msg)
        except discord.errors.Forbidden:
            c.botlog('Forbidden: %s // %s: %s' % (ctx.message.server, ctx.message.channel.id, error))
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        c.botlog('Argument: %s // %s: %s' % (ctx.message.author, ctx.message.content, error))

        msg = await bot.send_message(
            ctx.message.channel,
            content='*this command requires more arguments. try `>help [cmd]`*'
        )
        await asyncio.sleep(7)
        await bot.delete_message(msg)
    elif isinstance(error, commands.errors.CommandNotFound):
        c.botlog('NotFound/Forbidden: %s/%s // %s: %s' % (
            ctx.message.server.id, ctx.message.channel, ctx.message.content, error
        ))
    else:
        raise error


def reorder(string_in):
    """Reorders a string. Called iteratively to give scrolling effect."""

    string_out = string_in[1:] + string_in[0]
    return string_out


@bot.event
async def change_status():
    """Slow scrolling effect for "Playing" status message."""

    await bot.wait_until_ready()

    # status to scroll (about 25 characters recommended)
    current_status = 'crimsoBOT is watching...'
    while not bot.is_closed:
        current_status = reorder(current_status)
        await bot.change_presence(game=discord.Game(name=current_status))
        await asyncio.sleep(7)


@bot.event
async def reminder():
    """"Sends a disappearing random reminder in default channel."""

    await bot.wait_until_ready()

    # open reminder text file, strip newlines at end
    reminder_list = open(c.clib_path_join('text', 'reminders.txt'),
                         encoding='utf-8', errors='ignore').readlines()
    reminder_list = [line[:-1] for line in reminder_list]
    reminder_list = [line.replace('\\n', '\n') for line in reminder_list]

    channel_list = [
        discord.Object(id='280298381807714304'),  # ooer
        # discord.Object(id='552650673418797069'), # crimso
        # discord.Object(id='445699717842731011'), # BCP
    ]

    # send in current channel on startup, and then...
    while not bot.is_closed:
        # calc time to next msg
        time_until = int(random.gauss(900, 90))
        await asyncio.sleep(time_until)

        # then send to each channel in list
        for channel in channel_list:
            msg = await bot.send_message(channel, random.choice(reminder_list))

            # delete after 10s if no reaction
            await asyncio.sleep(10)
            cache_msg = discord.utils.get(bot.messages, id=msg.id)
            if not cache_msg.reactions:
                await bot.delete_message(msg)


# channels to learn what crimso says
channel_list = [
    '552650673418797069',  # crimsoBOT/general
    '554799675912355861',  # crimsoBOT/botspam
    '280298381807714304',  # ooer/general
    '281918354133090305',  # ooer/serious
    '420809381735825418',  # ooer/botto
    '325969983441993729',  # ooer/botspam
]

banned_users = []


@bot.event
async def on_message(message):
    if c.is_banned(message.author.id):
        return

    # DM logger
    dm = str(message.channel).startswith('Direct M')
    if dm and message.author.id != bot.user.id and not message.content.startswith('>'):  # crimsoBOT
        try:
            link = message.attachments[0]['url']
        except Exception:
            link = ''

        await bot.send_message(
            discord.Object(id='588708864363462656'),
            '`{} ({}):`\n{} {}'.format(message.channel, message.channel.id, message.content, link)
        )

    # process commands
    await bot.process_commands(message)

    # learn from crimso
    if message.author.id == '310618614497804289':
        if message.channel.id in channel_list:
            m.learner(message.content)

    # respond to ping
    if bot.user in message.mentions:
        await bot.send_message(message.channel, m.crimso())

    # random chat
    if random.random() < 0.001 and not dm:
        await bot.send_message(message.channel, m.crimso())


banned_servers = [
    '551596695138467853',
    '553727143629160453',
    '481246881310179339',
]


@bot.event
async def on_server_join(server):
    """Notify me when added to server"""

    if server.id in banned_servers:
        await bot.leave_server(server)
        c.botlog('Banned server {} attempted to add crimsoBOT.'.format(server.id))
        return

    c.botlog("Joined {server.owner}'s {server} [{server.id}]".format(server=server))

    embed = c.get_server_info_embed(server)

    # ...and send
    user = await bot.get_user_info('310618614497804289')  # is crimso
    try:
        await bot.send_message(user, 'Added to {server}'.format(server=server), embed=embed)
    except Exception:
        await bot.send_message(user, 'Added to {server}'.format(server=server))


def reboot(msg):
    c.botlog(msg)
    bot.close()
    os.execl('C:/Windows/System32/cmd.exe', '/k', '"D:/Python36/python.exe "' + PROJECT_DIR + '/bot.py"')


@bot.command(pass_context=True, hidden=True)
async def cboot_(ctx):
    if ctx.message.author.id == '310618614497804289':
        reboot('Rebooting...')


# load cogs (modules)
if __name__ == '__main__':
    for extension in extensions:
        try:
            bot.load_extension('crimsobot.cogs.{}'.format(extension))
        except Exception as error:
            c.botlog('{} cannot be loaded. [{}]'.format(extension, error))

# creat task for loop change_status
bot.loop.create_task(change_status())

# create task for reminder
# bot.loop.create_task(reminder())

while True:
    try:
        bot.close()
        bot.run(TOKEN, reconnect=True)
    except Exception:
        reboot('Connection error encountered! Retrying...')

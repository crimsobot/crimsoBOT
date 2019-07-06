import discord
from discord.ext import commands
import discord.errors as de
import asyncio
import datetime
import random
import math
import os

from config import TOKEN
import crimsobot.utils.tools as c
import crimsobot.utils.markov as m

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

bot = commands.Bot(command_prefix = '>')

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
    """Displays error messages to user for cooldown and CommandNotFound, and suppresses verbose error text for both in the console."""
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
        msg = await bot.send_message(ctx.message.channel, content='*this command requires more arguments. try `>help [cmd]`*')
        await asyncio.sleep(7)
        await bot.delete_message(msg)
    # elif isinstance(error, commands.errors.CommandNotFound):
    #     c.botlog('NotFound: %s/%s // %s: %s' % (ctx.message.author, ctx.message.server.id, ctx.message.content, error))
    elif isinstance(error, commands.errors.CommandNotFound):
        c.botlog('Forbidden: %s/%s // %s: %s' % (ctx.message.server.id, ctx.message.channel, ctx.message.content, error))
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
    reminderList = open(c.clib_path_join('text', 'reminders.txt'),
                        encoding='utf-8', errors='ignore').readlines()
    reminderList = [line[:-1] for line in reminderList]
    reminderList = [line.replace('\\n','\n') for line in reminderList]
    # send in current channel on startup, and then...
    while not bot.is_closed:
        channel_list = [discord.Object(id='280298381807714304'), # ooer
                        # discord.Object(id='552650673418797069'), # crimso
                        # discord.Object(id='445699717842731011'), # BCP
                       ]
        # calc time to next msg
        timeUntil = int(random.gauss(900,90))
        await asyncio.sleep(timeUntil)
        # then send to each channel in list
        for channel in channel_list:
            msg = await bot.send_message(channel,
                                         random.choice(reminderList))
            # delete after 10s if no reaction
            await asyncio.sleep(10)
            cache_msg = discord.utils.get(bot.messages, id=msg.id)
            if cache_msg.reactions == []:
                await bot.delete_message(msg)

# channels to learn what crimso says
channel_list = ['552650673418797069', # crimsoBOT/general
                '554799675912355861', # crimsoBOT/botspam
                '280298381807714304', # ooer/general
                '281918354133090305', # ooer/serious
                '420809381735825418', # ooer/botto
                '325969983441993729'] # ooer/botspam

banned_users = []

@bot.event
async def on_message(message):
    # if c.is_banned(message.author.id):
    #     return
    # DM logger
    dm = str(message.channel).startswith('Direct M')
    if dm == True and message.author.id != bot.user.id and message.content.startswith('>') == False: # crimsoBOT
        try:
            link = message.attachments[0]['url']
        except:
            link = ''
        await bot.send_message(discord.Object(id='588708864363462656'), '`{} ({}):`\n{} {}'.format(message.channel, message.channel.id, message.content, link))
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
    if random.random() < 0.001 and dm == False:
        await bot.send_message(message.channel, m.crimso())
    

banned_servers = ['551596695138467853',
                  '553727143629160453',
                  '481246881310179339']

@bot.event
async def on_server_join(server):
    """Notify me when added to server"""
    if server.id in banned_servers:
        await bot.leave_server(server)
        c.botlog('Banned server {} attempted to add crimsoBOT.'.format(server.id))
        return

    c.botlog("Joined {server.owner}'s {server} [{server.id}]".format(server=server))
    # initialize embed 
    embed = discord.Embed(title = server.name, description='**`{s}`** has `{m}` members, `{r}` roles and is owned by `{s.owner}`'.format(
                            s=server, m=len(server.members), r=len(server.roles)))
    # number of channels to show, which to show
    channel_list = [x for x in sorted(server.channels, key=lambda c: c.position) if x.type == discord.ChannelType.text]
    show = min(10,len(server.channels))
    embed.add_field(name = 'Channels ({}/{} shown)'.format(show, len(server.channels)),
                    value = '\n'.join([('· {channel.name}'.format(channel=channel)) for channel in channel_list[:show]]) or 'No channels.',
                    inline = False)
    # number of roles to show, which to show
    role_list = [x for x in sorted(server.roles, key=lambda r: r.position, reverse=True) if not x.is_everyone]
    show = min(10,len(role_list))
    # role_list = [x for x in server.roles if not x.is_everyone][0:10]
    embed.add_field(name = 'Roles ({}/{} shown)'.format(show, len(server.roles)-1), # minus 1 to not include @everyone
                    value = '\n'.join(['· {s}{name}'.format(s='@' if role.mentionable else '', name=role.name) for role in role_list[:show]]) or 'No roles.',
                    inline = False)
    # list emojis; truncate if need be
    show = len(server.emojis)
    total = show
    char_count = sum([len(emoji.name) for emoji in server.emojis])
    if char_count > 500:
        while char_count > 500:
            server.emojis = server.emojis[:-1]
            show = len(server.emojis)
            char_count = sum([len(emoji.name) for emoji in server.emojis])
    embed.add_field(name = 'Emojis ({}/{} shown)'.format(show, total),
                    value = ' '.join(['`:{e.name}:`'.format(e=emoji) for emoji in server.emojis[:show]]) or 'No custom emojis.',
                    inline = False)
    # footer, thumbnail
    embed.set_footer(text='Server ID: #{server.id}'.format(server=server))
    embed.set_thumbnail(url=server.icon_url)
    # ...and send
    user = await bot.get_user_info('310618614497804289') # is crimso
    try:
        await bot.send_message(user,'Added to {server}'.format(server=server),embed=embed)
    except:
        await bot.send_message(user,'Added to {server}'.format(server=server))

def reboot(msg):
    c.botlog(msg)
    bot.close()
    print(PROJECT_DIR)
    os.execl("C:/Windows/System32/cmd.exe", "/k",'"D:/Python36/python.exe "'+PROJECT_DIR+'/bot.py"')

@bot.command(pass_context=True, hidden=True)
async def cboot_(ctx):
    if ctx.message.author.id == '310618614497804289':
        reboot('Rebooting...')

#load cogs (modules)
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
    except:
        reboot('Connection error encountered! Retrying...')


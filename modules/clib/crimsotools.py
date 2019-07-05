import discord
from discord.ext import commands
import asyncio
import os
import pickle
import datetime
import sys

sys.modules['crimsotools'] = sys.modules[__name__]


class CrimsoBOTUser(object):
    pass

def fetch(userID):
    """ input: discord user ID
       output: CrimsoBOTUser object"""
    filename = clib_path_join('users', userID + '.pickle')
    # find user's file; if none exists, create it
    try:
        with open(filename, 'rb') as f:
            user = pickle.load(f)
    except FileNotFoundError:
        user = CrimsoBOTUser()
        user.ID = userID
    except OSError: # try again?
        with open(filename, 'rb') as f:
            user = pickle.load(f)
    return user

def close(user):
    """ input: crimsoBOT user object
       output: none"""
    filename = clib_path_join('users', user.ID + '.pickle')
    # pickle user's info
    try:
        with open(filename, 'wb') as f:
            pickle.dump(user, f)
    except OSError: # try again
        with open(filename, 'wb') as f:
            pickle.dump(user, f)

def botlog(event_string):
    """Log a string with timestamp to console and a text file."""
    stamp = '{n.year:04d}-{n.month:02d}-{n.day:02d} {n.hour:02d}:{n.minute:02d}:{n.second:02d} | {ev}'.format(n=datetime.datetime.now(), ev=event_string)
    print(stamp)
    with open(clib_path_join('text', 'botlog.txt'), 'a', encoding='utf-8', errors='ignore') as f:
        f.write(stamp+'\n')

def checkin(cmd, serverName, channel, running):
    """Is game already running in channel/DM?"""
    if channel.id in running:
        return False
    else:
        running.append(channel.id)
        if serverName is None:
            serverName = '*'
        print('----IN PROGRESS---- | {} running on {}/{} ({})...'.format(cmd, serverName, channel, channel.id))

def checkout(cmd, serverName, channel, running):
    """Is game already running in channel/DM?"""
    running.remove(channel.id)
    if serverName is None:
        serverName = '*'
    botlog(cmd+' COMPLETE on {}/{}!'.format(serverName, channel))
    
def crimbed(title, description, thumbnail=None, color=0x5AC037):
    embed = discord.Embed(title=title, description=description, color=color)
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)
    return embed

def crimsplit(long_string, break_char, limit=2000):
    """Break a string."""
    list_of_strings = []
    while len(long_string) > limit:
        # find indexes of all break_chars; if no break_chars, index = limit
        index = [i for i, brk in enumerate(long_string) if brk == break_char]
        if index == [] or max(index) < limit:
            index.append(limit)
        # find first index at or past limit, break message
        for ii in range(0, len(index)):
            if index[ii] >= limit:
                list_of_strings.append(long_string[:index[ii-1]].lstrip(' '))
                long_string = long_string[index[ii-1]:]
                break # back to top, if long_string still too long
    # include last remaining bit of long_string and return
    list_of_strings.append(long_string)
    return list_of_strings

def ban(discord_user_id):
    cb_user_object = fetch(discord_user_id)
    cb_user_object.banned = True
    close(cb_user_object)

def unban(discord_user_id):
    cb_user_object = fetch(discord_user_id)
    cb_user_object.banned = False
    close(cb_user_object)

def is_banned(discord_user_id):
    cb_user_object = fetch(discord_user_id)
    try:
        return cb_user_object.banned
    except AttributeError:
        return False

def who_is_banned():
    """ input: none
       output: sorted list of CrimsoBOTUser objects"""
    cb_user_object_list = [] # list of CrimsoBOTUser objects
    filelist = [f for f in os.listdir(clib_path_join('users'))]
    for f in filelist:
        cb_user_object_list.append(fetch(f[:-7]))
    # remove attributeless
    for i in range(len(cb_user_object_list)):
        try:
            cb_user_object_list[i].banned
        except AttributeError:
            cb_user_object_list[i].banned = False
    cb_user_object_list = [user for user in cb_user_object_list if user.banned is True]
    return cb_user_object_list


def clib_path_join(*paths):
    clib_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(clib_path, *paths)

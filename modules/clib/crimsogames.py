import os
import random
import discord
from collections import Counter
from datetime import datetime
import crimsotools as c

# path to root
root_dir = os.path.dirname(__file__) #<-- absolute dir the script is in

def emojistring():
    """ input: none
       output: string"""
    emojis = []
    for line in open(root_dir+'\\emojilist.txt', encoding='utf-8', errors='ignore'):
        line = line.replace('\n','')
        emojis.append(line)
    emojis = ''.join(emojis)
    emoji_string = random.sample(emojis, random.randint(3,5))
    return ' '.join(emoji_string)

def tally(ballots):
    """ input: list
       output: tuple (string, int)"""
    c = Counter(sorted(ballots))
    winner = c.most_common(1)[0]
    return winner

def winner_list(winners):
    """ input: list of strings (or discord user objects!)
       output: string"""
    if len(winners) > 1:
        winners_ = ', '.join(winners[:-1])
        winners_ = winners_ + ' & ' + winners[-1] # winner, winner & winner
    else:
        winners_ = winners[0]
    return winners_

def getStory():
    story = open(root_dir+'\\madlibs.txt',
                encoding='utf-8', errors='ignore').readlines()
    story = [line[:-1] for line in story]
    story = [line.replace('\\n','\n') for line in story]
    return random.choice(story)

def getKeys(formatString):
    """formatString is a format string with embedded dictionary keys.
    Return a set containing all the keys from the format string."""
    keyList = list()
    end = 0
    repetitions = formatString.count('{')
    for i in range(repetitions):
        start = formatString.find('{', end) + 1 # pass the '{'
        end = formatString.find('}', start)
        key = formatString[start : end]
        keyList.append(key) # may add duplicates

    # find indices of marked tags (to be used more than once)
    ind = [i for i, s in enumerate(keyList) if '#' in s]
    # isolate the marked tags and keep one instance each
    mults = []
    for ele in ind:
        mults.append(keyList[ele])
    mults = list(set(mults))
    # delete all marked tags from original list
    for ele in sorted(ind, reverse = True):
        del keyList[ele]
    # ...and add back one instance each
    keyList = keyList + mults

    return keyList

def win(userID, amount):
    """ input: discord user ID, float
       output: none"""
    # make sure amount is numeric
    try:
        if not isinstance(amount, float):
            raise ValueError
    except ValueError:
        amount = float(amount)
    # get user    
    user = c.fetch(userID)
    # add coin; if no coin attribute, add it
    try:
        user.coin += amount
    except AttributeError:
        user.coin = amount
    # force round
    user.coin = round(user.coin, 2)
    c.close(user)

def daily(userID, lucky_number):
    """ input: discord user ID (string)
       output: string"""
    # fetch user
    user = c.fetch(userID)
    # get current time
    now = datetime.utcnow()
    # arbitrary "last date collected" and reset time (midnight UTC)
    reset = datetime(1969, 7, 20, 0, 0, 0) #ymd required but will not be used
    try:
        last = user.daily
    except AttributeError:
        last = reset
    # check if dates are same
    if last.strftime('%Y-%m-%d') == now.strftime('%Y-%m-%d'):
        hours = (reset - now).seconds / 3600
        minutes = (hours - int(hours)) * 60
        award_string = 'Daily award resets at midnight UTC, {}h{}m from now.'.format(int(hours), int(minutes + 1))
    else:
        winning_number = random.randint(1, 100)
        if winning_number == lucky_number:
            daily_award = 500
            jackpot = '**JACKPOT!** '
        else:
            daily_award = 10
            jackpot = 'The winning number this time was **{}**, but no worries: '.format(winning_number) if lucky_number != 0 else ''
        # update daily then close (save)
        user.daily = now
        c.close(user)
        # update their balance now (will repoen and reclose user)
        win(userID, daily_award)
        award_string = '{}You have been awarded your daily **\u20A2{:.2f}**!'.format(jackpot, daily_award)
    return award_string

def checkBalance(userID):
    """ input: discord user ID
       output: float"""    
    try:
        user = c.fetch(userID)
        # force round and close
        return round(user.coin, 2)
    except:
        return 0
    
def guess_economy(n):
    """ input: integer
       output: float, float"""
    # winnings for each n=0,...,20
    winnings = [0, 7, 2, 4, 7, 11, 15, 20, 25, 30, 36, 42, 49, 56, 64, 72, 80, 95, 120, 150, 200]
    # variables for cost function
    const = 0.0095 # dampener multiplier
    sweet = 8 # sweet spot for guess
    favor = 1.3 # favor to player (against house) at sweet spot
    # conditionals
    if n > 2:
        cost = winnings[n]/n - (-const*(n-sweet)**2 + favor)
    else:
        cost = 0.00
    return winnings[n], cost

def guess_luck(userID, n, win):
    user = c.fetch(userID)
    try:
        user.guess_plays += 1
    except AttributeError:
        user.guess_plays = 1
    try:
        user.guess_expected += 1/n
    except AttributeError:
        user.guess_expected = 1/n
    try:
        user.guess_wins += win
    except AttributeError:
        user.guess_wins = win
    user.guess_luck = user.guess_wins / user.guess_expected
    c.close(user)

def guess_luck_balance(userID):
    try:
        user = c.fetch(userID)
        return user.guess_luck, user.guess_plays
    except AttributeError:
        return 0, 0

def leaders(place1, place2, trait='coin'):
    """ input: int, int
       output: sorted list of CrimsoBOTUser objects"""
    cb_user_object_list = [] # list of CrimsoBOTUser objects
    filelist = [f for f in os.listdir('D://Dropbox (Personal)//Personal//Python//crimsoBOT//users')]
    for f in filelist:
        cb_user_object_list.append(c.fetch(f[:-7]))
    # remove attributeless
    for user in cb_user_object_list[:]:
        try:
            if trait == 'coin':
                user.coin
            elif trait == 'luck' or 'plays':
                user.guess_wins # either trait, they'll have this attribute
        except AttributeError:
            cb_user_object_list.remove(user)
    # sort list of objects by coin
    if trait == 'coin':
        cb_user_object_list = [user for user in cb_user_object_list if user.coin > 0]
        cb_user_object_list.sort(key=lambda x: x.coin, reverse=True)
    elif trait == 'luck':
        cb_user_object_list = [user for user in cb_user_object_list if user.guess_plays > 49]
        cb_user_object_list.sort(key=lambda x: x.guess_luck, reverse=True)
    elif trait == 'plays':
        cb_user_object_list = [user for user in cb_user_object_list if user.guess_plays != 0]
        cb_user_object_list.sort(key=lambda x: x.guess_plays, reverse=True)
    return cb_user_object_list[place1-1:place2]

def guesslist():
    """ input: none
       output: string"""
    output = [' n  ·   cost   ·   payout',
              '·························']
    for i in range(2,21):
        spc='\u2002' if i < 10 else ''
        w, c = guess_economy(i)
        output.append('{}{:>d}  ·  \u20A2{:>5.2f}  ·  \u20A2{:>6.2f}'.format(spc, i, c, w))
    output = '\n'.join(output)
    return output

# def slot_helper(bets):
#     """ input: integer
#        output: string"""
#     machine = [':arrow_lower_right:│:blank:│:blank:│:blank:│:five:\n' +
#                ':arrow_two:│11│12│13│:two:\n' +
#                ':arrow_right:│21│22│23│:one:\n' +
#                ':arrow_three:│31│32│33│:three:\n' +
#                ':arrow_upper_right:│:blank:│:blank:│:blank:│:four:']
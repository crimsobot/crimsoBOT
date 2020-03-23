import random
from collections import Counter
from datetime import datetime
from typing import List, Optional, Set, Tuple, Union

import discord

from discord import Embed

from crimsobot.models.currency_account import CurrencyAccount
from crimsobot.models.guess_statistic import GuessStatistic
from crimsobot.utils import tools as c

DiscordUser = Union[discord.User, discord.Member]


def emojistring() -> str:
    emojis = []
    for line in open(c.clib_path_join('games', 'emojilist.txt'), encoding='utf-8', errors='ignore'):
        line = line.replace('\n', '')
        emojis.append(line)

    emoji_string = random.sample(''.join(emojis), random.randint(3, 5))

    return ' '.join(emoji_string)


def tally(ballots: List[str]) -> Tuple[str, int]:
    counter = Counter(sorted(ballots))
    winner = counter.most_common(1)[0]

    return winner


def winner_list(winners: List[str]) -> str:
    if len(winners) > 1:
        winners_ = ', '.join(winners[:-1])
        winners_ = winners_ + ' & ' + winners[-1]  # winner, winner & winner
    else:
        winners_ = winners[0]

    return winners_


def get_story() -> str:
    story = open(
        c.clib_path_join('games', 'madlibs.txt'),
        encoding='utf-8',
        errors='ignore'
    ).readlines()

    story = [line[:-1] for line in story]
    story = [line.replace('\\n', '\n') for line in story]

    return random.choice(story)


def get_keys(format_string: str) -> List[str]:
    """format_string is a format string with embedded dictionary keys.
    Return a set containing all the keys from the format string."""

    keys = []
    end = 0
    repetitions = format_string.count('{')
    for _ in range(repetitions):
        start = format_string.find('{', end) + 1  # pass the '{'
        end = format_string.find('}', start)
        key = format_string[start:end]
        keys.append(key)  # may add duplicates

    # find indices of marked tags (to be used more than once)
    ind = [i for i, s in enumerate(keys) if '#' in s]

    # isolate the marked tags and keep one instance each
    mults = []
    for ele in ind:
        mults.append(keys[ele])
    mults = list(set(mults))

    # delete all marked tags from original list
    for ele in sorted(ind, reverse=True):
        del keys[ele]

    # ...and add back one instance each
    keys = keys + mults

    return keys


async def win(discord_user: DiscordUser, amount: float) -> None:
    account = await CurrencyAccount.get_by_discord_user(discord_user)  # type: CurrencyAccount
    account.add_to_balance(amount)
    await account.save()


async def daily(discord_user: DiscordUser, lucky_number: int) -> Embed:
    # fetch account
    account = await CurrencyAccount.get_by_discord_user(discord_user)  # type: CurrencyAccount

    # get current time
    now = datetime.utcnow()

    # arbitrary "last date collected" and reset time (midnight UTC)
    reset = datetime(1969, 7, 20, 0, 0, 0)  # ymd required but will not be used

    last = account.ran_daily_at

    # check if dates are same; if so, gotta wait
    if last and last.strftime('%Y-%m-%d') == now.strftime('%Y-%m-%d'):
        hours = (reset - now).seconds / 3600
        minutes = (hours - int(hours)) * 60

        title = "Patience..."
        award_string = "Daily award resets at midnight UTC, {}h{}m from now.".format(int(hours), int(minutes + 1))
        thumb = "clock"
        color = "orange"
    # if no wait, then check if winner or loser
    else:
        winning_number = random.randint(1, 100)

        if winning_number == lucky_number:
            daily_award = 500
        
            title = "JACKPOT!"
            wrong = ""  # they're not wrong!
            thumb = "moneymouth"
            color = "green"

        else:
            daily_award = 10
        
            title_choices = [
                "*heck*",
                "*frick*",
                "*womp womp*",
                "**😩**",
                "Aw shucks.",
                "Why even bother?",
            ]
            title = random.choice(title_choices)
            wrong = "The winning number this time was **{}**, but no worries:".format(winning_number)
            thumb = "crimsoCOIN"
            color = "yellow"

        # update daily then save
        account.ran_daily_at = now
        await account.save()

        # update their balance now (will repoen and reclose user)
        await win(discord_user, daily_award)

        award_string = "{} You have been awarded your daily **\u20A2{:.2f}**!".format(wrong, daily_award)
        thumb = thumb
        color = color
    
    # the embed to return
    embed = c.crimbed(
        title=title,
        descr=award_string,
        thumb_name=thumb,
        color_name=color,
    )
    return embed


async def check_balance(discord_user: DiscordUser) -> float:
    account = await CurrencyAccount.get_by_discord_user(discord_user)  # type: CurrencyAccount

    return account.get_balance()


def guess_economy(n: int) -> Tuple[float, float]:
    """ input: integer
       output: float, float"""

    # winnings for each n=0,...,20
    winnings = [0, 7, 2, 4, 7, 11, 15, 20, 25, 30, 36, 42, 49, 56, 64, 72, 80, 95, 120, 150, 200]

    # variables for cost function
    const = 0.0095  # dampener multiplier
    sweet = 8  # sweet spot for guess
    favor = 1.3  # favor to player (against house) at sweet spot

    # conditionals
    if n > 2:
        cost = winnings[n] / n - (-const * (n - sweet) ** 2 + favor)
    else:
        cost = 0.00

    return winnings[n], cost


async def guess_luck(discord_user: DiscordUser, n: int, won: bool) -> None:
    stats = await GuessStatistic.get_by_discord_user(discord_user)  # type: GuessStatistic

    stats.plays += 1
    stats.add_to_expected_wins(n)
    if won:
        stats.wins += 1

    await stats.save()


async def guess_luck_balance(discord_user: DiscordUser) -> Tuple[float, int]:
    stats = await GuessStatistic.get_by_discord_user(discord_user)  # type: GuessStatistic

    return stats.luck_index, stats.plays


def guesslist() -> str:
    output = [' n  ·   cost   ·   payout',
              '·························']
    for i in range(2, 21):
        spc = '\u2002' if i < 10 else ''
        w, c = guess_economy(i)
        output.append('{}{:>d}  ·  \u20A2{:>5.2f}  ·  \u20A2{:>6.2f}'.format(spc, i, c, w))

    return '\n'.join(output)

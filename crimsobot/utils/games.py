import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import Any, List, Tuple, Union

import discord
from discord import Embed
from discord.ext import commands

from crimsobot.data.games import DAILY_RULES
from crimsobot.exceptions import NotAnInteger, OutOfBounds
from crimsobot.models.currency_account import CurrencyAccount
from crimsobot.models.guess_statistic import GuessStatistic
from crimsobot.utils import tools as c

DiscordUser = Union[discord.User, discord.Member]


def get_crimsoball_answer(ctx: commands.Context) -> str:  # function to give first answer a ctx to work with
    # don't know if this is any better than just putting it
    # inside of the crimsoball command
    answer_list = [
            '{} haha ping'.format(ctx.message.author.mention),
            'ye!',
            '**no**',
            'what do you think?',
            '*perhaps*',
            'OMAN',
            "i can't answer this, you need an adult",
            'absolutely!\n\n\n`not`',
            'of course!',
            'according to quantum superposition, the answer was both yes and no before you asked.',
            "is the sky blue?\n\n(is it? i don't know. i don't have eyes.)",
            "i can't be bothered with this right now.",
            'funny you should ask--',
            'fine, sure, whatever',
            '<:xok:551174281367650356>',
            'ask seannerz. ping him now and ask.',
            'ehhhh sure',
            'hmmmm. no.',
            'uhhhhhhhhh',
            '<:uhhhh:495249068789071882>',
            'eat glass!',
            'it is important that you stop bothering me.',
            'you CANNOT be serious',
            'sure? how would i know?',
            'what heck',
            'random_response',  # leave this alone
        ]

    return random.choice(answer_list)


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


async def win(discord_user: DiscordUser, amount: float) -> None:
    account = await CurrencyAccount.get_by_discord_user(discord_user)  # type: CurrencyAccount
    account.add_to_balance(amount)
    await account.save()

# simple_eval() by MestreLion via StackOverflow with changes in exception handling
# https://stackoverflow.com/a/65945969

# Kept outside simple_eval() just for performance
_re_simple_eval = re.compile(rb'd([\x00-\xFF]+)S\x00')


def simple_eval(expr: str) -> Any:
    try:
        c = compile(expr, 'userinput', 'eval')
    except SyntaxError:
        raise SyntaxError(f'Malformed expression: {expr}')

    m = _re_simple_eval.fullmatch(c.co_code)

    if not m:
        raise SyntaxError(f'Not a simple algebraic expression: {expr}')

    try:
        return c.co_consts[int.from_bytes(m.group(1), sys.byteorder)]
    except IndexError:
        raise SyntaxError(f'Expression not evaluated as constant: {expr}')


def integer_in_range(number: Any, low: int, high: int) -> Any:
    # is 'number' a number?
    try:
        number = float(number)
    except ValueError:
        raise ValueError(f'{number} is not a number!')
    except TypeError:
        raise ValueError(f'{number} is not a number!')

    # is 'number' (close enough to) an integer?
    try:
        delta = abs(number - round(number))
        if delta > 1e-10:  # arbitrary limit
            raise NotAnInteger(str(number))
    except OverflowError:  # e.g. infinity will fail at delta
        raise OutOfBounds(str(number))

    # is 'number' in range?
    if not low <= number <= high:
        raise OutOfBounds(str(int(number)))

    # enforce type
    number = int(number)

    return number


async def daily(discord_user: DiscordUser, guess: str) -> Embed:
    # is the guess in range?
    try:
        lucky_number = integer_in_range(guess, 1, 100)
    # if the guess is not already a positive integer [1 - 100]...
    except ValueError:
        # ...first check if it's a math expression...
        try:
            lucky_number = simple_eval(guess)

            # but if the answer is not an integer 1-100...
            lucky_number = integer_in_range(lucky_number, 1, 100)
        # ...and if it's bounced from simple_eval(), try it as a string
        except SyntaxError:
            # find sum of remaining characters
            lucky_number = 0

            for char in guess.lower():
                if char.isalpha():
                    # this will effectively bounce everything except lowercase a-z
                    lucky_number += (ord(char) - 96)
                elif char.isnumeric():
                    lucky_number += int(char)
                else:
                    pass

            lucky_number = integer_in_range(lucky_number, 1, 100)
        # final catchment for strings with sums outside of bounds
        except ValueError:  # the last bastion
            raise OutOfBounds(str(lucky_number))

    # fetch account
    account = await CurrencyAccount.get_by_discord_user(discord_user)  # type: CurrencyAccount

    # get current time and time last run
    now = datetime.utcnow()
    now = datetime.now(timezone.utc)
    last = account.ran_daily_at

    # check if dates are same; if so, gotta wait
    if last and last.strftime('%Y-%m-%d') == now.strftime('%Y-%m-%d'):
        title = random.choice(DAILY_RULES['not_yet'])
        award_string = 'The Daily game resets at midnight UTC.'
        thumb = 'clock'
        color = 'orange'
        footer = None

    # if no wait, then check if winner or loser
    else:
        winning_number = random.randint(1, 100)

        if winning_number == lucky_number:
            daily_award = DAILY_RULES['award']['win']

            title = 'JACKPOT!'
            if_wrong = ''  # they're not wrong!
            thumb = 'moneymouth'
            color = 'green'
            footer = f'Your guess: {lucky_number} · Congratulations!'

        else:
            daily_award = DAILY_RULES['award']['lose']

            title = random.choice(DAILY_RULES['wrong_guess'])
            if_wrong = f'The winning number this time was **{winning_number}**. '
            thumb = 'crimsoCOIN'
            color = 'yellow'
            footer = f'Your guess: {lucky_number} · Thanks for playing!'

        # update daily then save
        account.ran_daily_at = now
        await account.save()

        # update their balance now (will repoen and reclose user)
        await win(discord_user, daily_award)

        # finish up the award string with amount won
        award_string = f'{if_wrong}You have been awarded **\u20A2{daily_award:.2f}**!'

    # embed to return
    embed = c.crimbed(
        title=title,
        descr=award_string,
        thumb_name=thumb,
        color_name=color,
        footer=footer,
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


# async def guess_luck_balance(discord_user: DiscordUser) -> Tuple[float, int]:
#     stats = await GuessStatistic.get_by_discord_user(discord_user)  # type: GuessStatistic

#     return stats.luck_index, stats.plays

async def guess_stat_embed(user: DiscordUser) -> Embed:
    """Return a big ol' embed of Guessmoji! stats"""

    s = await GuessStatistic.get_by_discord_user(user)

    if s.plays == 0:
        embed = c.crimbed(
            title='HOW—',
            descr="You haven't played GUESSMOJI! yet!",
            thumb_name='weary',
            footer='Play >guess [n] today!',
        )
    else:
        embed = c.crimbed(
            title='GUESSMOJI! stats for {}'.format(user.name),
            descr=None,
            thumb_name='crimsoCOIN',
            footer='Stat tracking as of {d.year}-{d.month:02d}-{d.day:02d}'.format(d=s.created_at),
        )

        ess = '' if s.plays == 1 else 's'
        ess2 = '' if s.wins == 1 else 's'

        # list of tuples (name, value) for embed.add_field
        field_list = [
            (
                'Gameplay',
                '**{}** game{ess} played, **{}** win{ess2}'.format(s.plays, s.wins, ess=ess, ess2=ess2)
            ),
            (
                'Luck index (expected: 100)',
                '**{:.3f}**'.format(100 * s.luck_index)
            ),
        ]

        for field in field_list:
            embed.add_field(name=field[0], value=field[1], inline=False)

    return embed


def guesslist() -> str:
    output = [' n  ·   cost   ·   payout',
              '·························']
    for i in range(2, 21):
        spc = '\u2002' if i < 10 else ''
        w, c = guess_economy(i)
        output.append('{}{:>d}  ·  \u20A2{:>5.2f}  ·  \u20A2{:>6.2f}'.format(spc, i, c, w))

    return '\n'.join(output)

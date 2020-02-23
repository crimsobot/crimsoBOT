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


class Cringo:
    def __init__(self, player: discord.Member, card: List[List[str]], score: int, matches: Set[str], mismatch_count: int):
        self.player = player
        self.card = card
        self.score = score
        self.matches = matches
        self.mismatch_count = mismatch_count


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


async def daily(discord_user: DiscordUser, lucky_number: int) -> str:
    # fetch account
    account = await CurrencyAccount.get_by_discord_user(discord_user)  # type: CurrencyAccount

    # get current time
    now = datetime.utcnow()

    # arbitrary "last date collected" and reset time (midnight UTC)
    reset = datetime(1969, 7, 20, 0, 0, 0)  # ymd required but will not be used

    last = account.ran_daily_at

    # check if dates are same
    if last and last.strftime('%Y-%m-%d') == now.strftime('%Y-%m-%d'):
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
            jackpot = 'The winning number this time was **{}**, but no worries: '.format(
                winning_number) if lucky_number != 0 else ''

        # update daily then save
        account.ran_daily_at = now
        await account.save()

        # update their balance now (will repoen and reclose user)
        await win(discord_user, daily_award)
        award_string = '{}You have been awarded your daily **\u20A2{:.2f}**!'.format(jackpot, daily_award)

    return award_string


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


async def cringo_instructions() -> Embed:
    """Embed with Cringo! instructions to send to each user"""

    embed = c.crimbed(
        title='Welcome to **CRINGO!**',
        description="""
            Match the emojis called to the emojis on your card.
            If you see a match, type the column and row of the match!
            Type `.<letter><number>` or `. <letter><number>`.
            You can put in multiple matches separated by a space!
            For example: `.a1 b2 c4` or `. b4 c3`. Only use one period!
            Missed a match on a previous turn? No problem! Put it in anyway.
            You'll still get your points (but with a lower multiplier).
            Check your score in between turns in the channel. Good luck!
            """,
        thumbnail='https://i.imgur.com/gpRToBn.png'  # jester
    )

    return embed


async def cringo_emoji(number_of_rows: int, already_used: List[str] = None) -> List[List[str]]:
    """Single row of emojis for game turn, four rows for game card"""

    # list of lists of emojis
    game_emojis = [
        ['🤠', '😂', '😍', '😋', '🤑', '🤔', '😎', '😔', '🤢', '😡'],
        ['🐴', '🐈', '🐙', '🐺', '🦛', '🐼', '🐸', '🐍', '🐌', '🐝'],
        ['🍉', '🍋', '🍒', '🥑', '🍆', '🍄', '🥞', '🍕', '🧀', '🧄'],
        ['💞', '💯', '🎵', '🚱', '💊', '🛐', '♻️', '🎈', '💤', '🔋'],
    ]

    # remove all emojis that have already been used
    if already_used is not None:
        # go through each list to eliminate already-used emojis
        for row in range(0, len(game_emojis)):
            game_emojis[row] = [x for x in game_emojis[row] if x not in already_used]

    # randomly select an emoji for each column x the number of rows requested
    selected_emojis = []
    number_of_columns = len(game_emojis)

    for col in range(0, number_of_columns):
        # take one random sample from each column
        selected_emojis.append(random.sample(game_emojis[col], number_of_rows))

    # reshape list of lists into the columns of the card/turn using zip
    selected_emojis = [list(x) for x in zip(*selected_emojis)]

    return selected_emojis


async def cringo_card(list_of_emojis: List[List[str]]) -> List[List[str]]:
    """This makes the Cringo! card complete with headers."""

    top_row = ['🇦', '🇧', '🇨', '🇩']
    side_column = ['<:lemonface:623315737796149257>', '1️⃣', '2️⃣', '3️⃣', '4️⃣']

    list_of_emojis.insert(0, top_row)

    emojis_to_send = []

    for row in range(0, len(list_of_emojis)):
        list_of_emojis[row].insert(0, side_column[row])
        emoji_string = '\u200A'.join(list_of_emojis[row])
        emojis_to_send.append(emoji_string)

    return list_of_emojis


async def deliver_card(list_of_lists: List[List[str]]) -> str:
    """Let's make it pretty!"""

    final_string = []
    for sublist in list_of_lists:
        final_string.append('\u200A'.join(sublist))

    # add blank emoji to first line to accommodate compact mode w/o resizing emojis
    return '<:blank:589560784485613570>\n'+'\n'.join(final_string)


async def mark_card(player: Cringo, position: str, emojis_to_check: List[str]) -> bool:
    """
    "Marks" the card with a star if there's a match.
    The card is a list of lists, formatted as such:
        [
            [ ...headers... ],
            [...,a1,b1,c1,d1],
            [...,a2,b2,c2,d2],
            [...,a3,b3,c3,d3],
            [...,a4,b4,c4,d4]
        ]
    """

    # card dict
    sublist = {'1': 1, '2': 2, '3': 3, '4': 4}
    item = {'a': 1, 'b': 2, 'c': 3, 'd': 4}

    # in case message begins with a period but has invalid keys
    try:
        # format the string from user that contains position
        indices = position.strip()
        col_abcd = indices[-2].lower()  # corresponds to item
        row_1234 = indices[-1]          # corresponds to sublist
        selected_emoji = player.card[sublist[row_1234]][item[col_abcd]]
    except KeyError:
        return False
    except IndexError:
        player.mismatch_count += 1
        return False

    # check for match
    is_match = selected_emoji in emojis_to_check and selected_emoji in (emoji for sublist in player.card for emoji in sublist)
    if is_match:
        player.card[sublist[row_1234]][item[col_abcd]] = '⭐'
        return True
    else:
        player.mismatch_count += 1
        return False


async def cringo_score(player: Cringo, turn_number: int, multiplier: int) -> None:
    """
    Determine how many points to award based on match.

    Possible matches:
        Columns A, B, C, D
        Row 1, 2, 3, 4
        Diag NW-SE, SW-NE
        ...and full house, of course.

    The card is a list of lists, formatted as such:
        [
            [ ...headers... ],
            [...,a1,b1,c1,d1],
            [...,a2,b2,c2,d2],
            [...,a3,b3,c3,d3],
            [...,a4,b4,c4,d4]
        ]
    """

    # look at the card for matches, first within-list (rows)
    if '1' not in player.matches:
        if player.card[1].count('⭐') == 4:
            player.matches.add('1')
            player.score += 100 * multiplier
    if '2' not in player.matches:
        if player.card[2].count('⭐') == 4:
            player.matches.add('2')
            player.score += 100 * multiplier
    if '3' not in player.matches:
        if player.card[3].count('⭐') == 4:
            player.matches.add('3')
            player.score += 100 * multiplier
    if '4' not in player.matches:
        if player.card[4].count('⭐') == 4:
            player.matches.add('4')
            player.score += 100 * multiplier

    # then look for diagonals
    if 'D1' not in player.matches:
        if player.card[1][1] == player.card[2][2] == player.card[3][3] == player.card[4][4]:
            player.matches.add('D1')
            player.score += 100 * multiplier
    if 'D2' not in player.matches:
        if player.card[4][1] == player.card[3][2] == player.card[2][3] == player.card[1][4]:
            player.matches.add('D2')
            player.score += 100 * multiplier

    # then look for column matches
    if 'A' not in player.matches:
        if player.card[1][1] == player.card[2][1] == player.card[3][1] == player.card[4][1]:
            player.matches.add('A')
            player.score += 100 * multiplier
    if 'B' not in player.matches:
        if player.card[1][2] == player.card[2][2] == player.card[3][2] == player.card[4][2]:
            player.matches.add('B')
            player.score += 100 * multiplier
    if 'C' not in player.matches:
        if player.card[1][3] == player.card[2][3] == player.card[3][3] == player.card[4][3]:
            player.matches.add('C')
            player.score += 100 * multiplier
    if 'D' not in player.matches:
        if player.card[1][4] == player.card[2][4] == player.card[3][4] == player.card[4][4]:
            player.matches.add('D')
            player.score += 100 * multiplier
    
    # full house
    if 'full' not in player.matches:
        if len(player.matches) == 10:
            player.matches.add('full')
            player.score += 1000 * multiplier

    # feels like that could be more elegantly-written, no?
    # TODO: yes

    return None


async def cringo_scoreboard(players: List[Cringo]) -> str:
    """Unpack the player objects to get something that can be sorted and displayed."""

    scoreboard = []
    for player in players:
        scoreboard.append([player.player, player.score])

    # sort in place
    scoreboard.sort(key=lambda inner_index: inner_index[1], reverse=True)

    scoreboard_list = []
    for line in scoreboard:
        scoreboard_list.append('{} · **{}** points'.format(line[0], line[1]))

    return '\n'.join(scoreboard_list)

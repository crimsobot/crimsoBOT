import dataclasses
import random
from typing import List, Set, Union

import discord
from discord import Embed

from crimsobot.models.cringo_statistic import CringoStatistic
from crimsobot.utils import tools as c

DiscordUser = Union[discord.User, discord.Member]


# See https://stackoverflow.com/questions/53632152 for info on usage of field
@dataclasses.dataclass
class CringoPlayer:
    user: discord.Member = None
    card: List[List[str]] = dataclasses.field(default_factory=list)
    score: int = 0
    matches: int = 0
    lines: Set[str] = dataclasses.field(default_factory=set)
    full_card: int = 0
    mismatch_count: int = 0
    winnings: float = 0


# no clue where to put this, so here goes
raw_cringo_emojis = [
    [
        '<:cringo_01:693934587705032857>', '<:cringo_02:693934619804041297>',
        '<:cringo_03:693934628586913932>', '<:cringo_04:693934628523868260>',
        '<:cringo_05:693934628565942302>', '<:cringo_06:693934628221747292>'
    ],
    [
        '<:cringo_07:693934628737646642>', '<:cringo_08:693934625931657317>',
        '<:cringo_09:693934622568087582>', '<:cringo_10:693934622605574245>',
        '<:cringo_11:693934628335124572>', '<:cringo_12:693934628121346089>'
    ],
    [
        '<:cringo_13:693934628511154306>', '<:cringo_14:693934625461895180>',
        '<:cringo_15:693934613957181451>', '<:cringo_16:693934614212771931>',
        '<:cringo_17:693934623998083083>', '<:cringo_18:693934628805017627>'
    ],
    [
        '<:cringo_19:693934628679057449>', '<:cringo_20:693934628981178399>',
        '<:cringo_21:693934628649566219>', '<:cringo_22:693934628305895475>',
        '<:cringo_23:693934628855218216>', '<:cringo_24:693934628938973265>'
    ],
    [
        '<:cringo_25:693934628888641536>', '<:cringo_26:693934629001887805>',
        '<:cringo_27:693934629086036018>', '<:cringo_28:693934628637245480>',
        '<:cringo_29:693934628968464475>', '<:cringo_30:693934628796629053>'
    ],
    [
        '<:cringo_31:693934629048025108>', '<:cringo_32:693934628800692276>',
        '<:cringo_33:693934629119459459>', '<:cringo_34:693934629127979009>',
        '<:cringo_35:693934629027184650>', '<:cringo_36:693934629060870194>'
    ]
]


async def cringo_emoji(number_of_rows: int, number_of_columns: int, already_used: List[str] = None) -> List[List[str]]:
    """Single row of emojis for game turn, four rows for game card"""

    # list of lists of emojis
    game_emojis = [
        ['🤠', '😂', '😍', '😋', '🤑', '🤔', '😎', '😔', '🤢', '😡'],
        ['🐴', '🐈', '🐙', '🐺', '🦛', '🐼', '🐸', '🐍', '🐌', '🐝'],
        ['🍉', '🍋', '🍒', '🥑', '🍆', '🍄', '🥞', '🍕', '🧀', '🧄'],
        ['💞', '💯', '🎵', '🚱', '💊', '🛐', '♻️', '🎈', '💤', '🔋'],
        ['🌹', '🌼', '🌴', '🏖️', '🍂', '🎃', '🎄', '❄️', '🌬️', '⛈️'],
        ['🔭', '🌖', '☄️', '🪐', '🌌', '👩‍🚀', '🛸', '👾', '🚀', '🛰️'],
    ]

    # remove all emojis that have already been used
    if already_used is not None:
        # go through each list to eliminate already-used emojis
        for row in range(0, number_of_columns):
            game_emojis[row] = [x for x in game_emojis[row] if x not in already_used]

    # randomly select an emoji for each column x the number of rows requested
    selected_emojis = []

    for col in range(0, number_of_columns):
        # take one random sample from each column
        selected_emojis.append(random.sample(game_emojis[col], number_of_rows))

    # reshape list of lists into the columns of the card/turn using zip
    selected_emojis = [list(x) for x in zip(*selected_emojis)]

    return selected_emojis


async def cringo_card(list_of_emojis: List[List[str]]) -> List[List[str]]:
    """This makes the Cringo! card complete with headers."""

    top_row = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫']
    side_column = ['<:lemonface:623315737796149257>', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']

    list_of_emojis.insert(0, top_row[0:len(list_of_emojis)])

    emojis_to_send = []

    for row in range(0, len(list_of_emojis)):
        list_of_emojis[row].insert(0, side_column[row])
        emoji_string = '\u200A'.join(list_of_emojis[row])
        emojis_to_send.append(emoji_string)

    return list_of_emojis


async def deliver_card(list_of_lists: List[List[str]]) -> str:
    """Let's make the Cringo! card pretty!"""

    final_string = []
    for sublist in list_of_lists:
        final_string.append('\u200A'.join(sublist))

    # add blank emoji to first line to accommodate compact mode w/o resizing emojis
    return '<:blank:589560784485613570>\n' + '\n'.join(final_string)


# this emoji marks the card
def marker(cardsize: int, row: int, column: int) -> str:
    """Returns which custom emoji to use to mark card."""

    # if card size = 2, only use the one marker: cringo_36
    if cardsize == 2:
        return raw_cringo_emojis[row + 1][column + 1]
    elif cardsize == 4:
        return raw_cringo_emojis[row][column]
    elif cardsize == 6:
        return raw_cringo_emojis[row - 1][column - 1]

    # no clue how we got here! but let's use cringo_36 just to be safe
    return raw_cringo_emojis[row + 1][column + 1]


async def mark_card(player: CringoPlayer, position: str, emojis_to_check: List[str], multiplier: int) -> bool:
    """Marks the card with a star if there's a match and adds to player score.
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
    rows: dict = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6}
    cols: dict = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}

    # a player's card has header rows and columns
    card_size = len(player.card) - 1

    # in case message begins with a period but has invalid keys
    try:
        # format the string from user that contains position
        indices = position.strip()
        col_abc = indices[-2].lower()  # corresponds to item
        row_123 = indices[-1]          # corresponds to sublist
        selected_emoji = player.card[rows[row_123]][cols[col_abc]]
    except KeyError:
        return False
    except IndexError:
        player.mismatch_count += 1
        return False

    # check for match
    check1 = selected_emoji in emojis_to_check
    check2 = selected_emoji in (emoji for sublist in player.card for emoji in sublist)
    match = check1 and check2

    if match:
        player.card[rows[row_123]][cols[col_abc]] = marker(card_size, rows[row_123], cols[col_abc])
        player.score += 10 * multiplier
        player.matches += 1
    else:
        player.mismatch_count += 1
        player.score -= player.mismatch_count

    # this bool used later to give feedback to user
    return match


async def cringo_score(player: CringoPlayer, turn_number: int, multiplier: int) -> None:
    """This function checks for and scores complete lines. mark_card() scores individual matches.

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

    # card dict
    rows: dict = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6}
    cols: dict = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}

    # how big is the card? remember card is square
    n = len(player.card[0]) - 1

    def line_score(direction: str, index: int = 0) -> bool:
        """Sort through rows or columns to check if all match."""

        # to keep from searching nonexistant rows and columns:
        if index >= n+1:
            return False

        # we skip the header row and column with (1,n)
        for i in range(1, n):
            if direction == 'row':
                if 'cringo' in player.card[index][i] and 'cringo' in player.card[index][i+1]:
                    pass
                else:
                    return False
            if direction == 'column':
                if 'cringo' in player.card[i][index] and 'cringo' in player.card[i+1][index]:
                    pass
                else:
                    return False
            if direction == 'LR':
                if 'cringo' in player.card[i][i] and 'cringo' in player.card[i+1][i+1]:
                    pass
                else:
                    return False
            if direction == 'RL':
                if 'cringo' in player.card[i][(n+1)-i] and 'cringo' in player.card[i+1][(n+1)-(i+1)]:
                    pass
                else:
                    return False

        return True

    # check all rows
    for row in rows:
        if row not in player.lines:
            complete_line = line_score('row', rows[row])
            if complete_line:
                player.lines.add(row)
                player.score += 100 * multiplier

    # then all columns
    for col in cols:
        if col not in player.lines:
            complete_line = line_score('column', cols[col])
            if complete_line:
                player.lines.add(col)
                player.score += 100 * multiplier

    # the two diagonals
    diagonals = ['LR', 'RL']
    for diag in diagonals:
        if diag not in player.lines:
            complete_line = line_score(diag)
            if complete_line:
                player.lines.add(diag)
                player.score += 100 * multiplier

    # and finally for a full house
    if 'full' not in player.lines:
        if len(player.lines) == n*2 + 2:
            player.lines.add('full')
            player.score += 1000 * multiplier
            player.full_card = 1


async def cringo_scoreboard(players: List[CringoPlayer], cursed: bool = False, game_finished: bool = False) -> str:
    """Unpack the player objects to get something that can be sorted and displayed."""

    scoreboard_rows = []
    for player in players:
        coin_display = 'zero' if cursed else player.winnings  # y'all dumb motherfuckers want a rounding error?
        if game_finished:
            row = f'{player.user} · **{player.score}** points · **{coin_display}** coin'
        else:
            row = f'{player.user} · **{player.score}** points'

        scoreboard_rows.append(row)

    return '\n'.join(scoreboard_rows)


async def cringo_stats(player: CringoPlayer, won: bool) -> None:
    stats = await CringoStatistic.get_by_discord_user(player.user)  # type: CringoStatistic

    # do not count stats if player did not "truly" play
    # minimum guaranteed matches = 12
    if player.matches < 12:
        return

    stats.plays += 1

    if won:
        stats.wins += 1

    stats.coin_won += player.winnings

    if player.score > stats.high_score:
        stats.high_score = player.score

    stats.total_score += player.score

    stats.matches += player.matches
    stats.lines += len(player.lines)
    stats.full_cards += player.full_card

    await stats.save()


async def cringo_stat_embed(user: DiscordUser) -> Embed:
    """Return a big ol' embed of Cringo! stats"""

    s = await CringoStatistic.get_by_discord_user(user)

    if s.plays == 0:
        embed = c.crimbed(
            title='Hold up—',
            descr="You haven't played any games of CRINGO yet!",
            thumb_name='jester',
            footer='Play >cringo today!',
        )
    else:
        embed = c.crimbed(
            title='CRINGO! stats for {}'.format(user),
            descr=None,
            thumb_name='jester',
            footer='Since {d.year}-{d.month:02d}-{d.day:02d} · Regular CRINGO! only'.format(d=s.created_at),
        )

        ess = '' if s.plays == 1 else 's'
        ess2 = '' if s.wins == 1 else 's'
        ess3 = '' if s.full_cards == 1 else 's'

        # list of tuples (name, value) for embed.add_field
        field_list = [
            (
                'Gameplay',
                '**{}** game{ess} played, **{}** win{ess2}'.format(s.plays, s.wins, ess=ess, ess2=ess2)
            ),
            (
                'crimsoCOIN won',
                '**\u20A2{:.2f}**'.format(s.coin_won)
            ),
            (
                'High score',
                '**{}** points'.format(s.high_score)
            ),
            (
                'Average score (expected: 2260)',
                '**{:.1f}** points/game'.format(s.mean_score)
            ),
            (
                'Matches/game (expected: 14.4)',
                '**{:.1f}** matches/game'.format(s.matches / s.plays)
            ),
            (
                'Lines/game: (expected: 6.34)',
                '**{:.2f}** lines/game'.format(s.lines / s.plays)
            ),
            (
                'Full cards (expected in {} game{ess}: {:.4f})'.format(s.plays, 0.1296 * s.plays, ess=ess),
                '**{}** full card{ess3}'.format(s.full_cards, ess3=ess3)
            ),
        ]

        for field in field_list:
            embed.add_field(name=field[0], value=field[1], inline=False)

    return embed

import random
from collections import Counter
from datetime import datetime
from typing import List, Optional, Set, Tuple, Union

import discord

from discord import Embed

from crimsobot.models.currency_account import CurrencyAccount
from crimsobot.models.guess_statistic import GuessStatistic
from crimsobot.utils import games as crimsogames
from crimsobot.utils import tools as c

DiscordUser = Union[discord.User, discord.Member]


class Cringo:
    def __init__(self):
        self.player: discord.Member = None
        self.card: List[List[str]] = None
        self.score: int = 0
        self.lines: Set[str] = set()
        self.mismatch_count: int = 0


# tools.checkin() used to prevent users from playing multiple cringo games at once
cringo_users = []


# first, a few helper functions to deal with players joining and leaving
async def player_remove(player_list: List[Cringo], player_object: Cringo) -> Embed:
    """Remove a user from list of players."""

    # remove from both the list of players for this game...
    player_list.remove(player_object)

    # ...as well as "global" list of messageables playing the game
    c.checkout(player_object.player, cringo_users)

    embed = c.crimbed(
        title=None,
        descr="{} has left the game.".format(player_object.player),
        color_name="yellow",
    )
    return embed


async def process_player_joining(player_list: List[Cringo], user_to_join: discord.User, min_bal: int = 0) -> Embed:
    """Processes player joining game and returns embed to send to game channel."""

    # first, check balance. cost is NOT debited.
    current_bal = await crimsogames.check_balance(user_to_join)
    cannot_play = current_bal < (min_bal if min_bal != 0 else float('-inf'))
    # ...this should let people with negative balance play regular CRINGO!

    if cannot_play:
        # these are passed to the embed_to_channel which is returned from this function
        title="Uh oh, **{} CANNOT** join the game!".format(user_to_join)
        descr="\n".join([
            "· You must have a balance of \u20A2{:.2f} to play this game!".format(min_bal),
            "· Don't fret; regular CRINGO! can be played by anyone!",
        ])
        color="orange"
        thumb="moneymouth"
    else:
        try:
            # if checkin fails, c.MessageableAlreadyJoined is raised
            c.checkin(user_to_join, cringo_users)

            # embed to DM to user to test if Forbidden
            embed_to_user = c.crimbed(
                title="Welcome to **CRINGO!**",
                descr="\n".join([
                    "Match the emojis called to the emojis on your card.",
                    "If you see a match, type the column and row of the match!",
                    "Type `.<letter><number>` or `. <letter><number>`.",
                    "You can put in multiple matches separated by a space!",
                    "For example: `.a1 b2 c4` or `. b4 c3`. Only use one period!",
                    "Missed a match on a previous turn? No problem! Put it in anyway.",
                    "You'll still get your points (but with a lower multiplier).",
                    "Check your score in between turns in the channel. Good luck!",
                ]),
                thumb_name="jester"
            )
            await user_to_join.send(embed=embed_to_user)
            
            # if neither raise an error, then player is added
            player_list.append(user_to_join)

            # these are passed to the embed_to_channel which is returned from this function
            title=None
            descr="**{}** has joined the game!".format(user_to_join)
            color="green"
            thumb=None

        except discord.errors.Forbidden:
            # user was checked in, so gotta check them out
            c.checkout(user_to_join, cringo_users)

            # these are passed to the embed_to_channel which is returned from this function
            title="Uh oh, **{} CANNOT** join the game!".format(user_to_join)
            descr="\n".join([
                "· You can't call CRINGO! from a DM!",
                "· You have to be able to receive DMs from crimsoBOT to play!",
            ])
            color="orange"
            thumb="weary"

        except c.MessageableAlreadyJoined:
            # these are passed to the embed_to_channel which is returned from this function
            title="Uh oh, **{} CANNOT** join the game!".format(user_to_join)
            descr="\n".join([
                "· Are you already playing Cringo! in another channel?",
            ])
            color="orange"
            thumb="think"

    embed_to_channel = c.crimbed(title=title, descr=descr, color_name=color, thumb_name=thumb)

    return embed_to_channel


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
        final_string.append("\u200A".join(sublist))

    # add blank emoji to first line to accommodate compact mode w/o resizing emojis
    return "<:blank:589560784485613570>\n"+"\n".join(final_string)


async def mark_card(player: Cringo, position: str, emojis_to_check: List[str], multiplier: int) -> bool:
    """
    "Marks" the card with a star if there's a match and adds to player score.
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
    is_match = check1 and check2

    match = True
    if is_match:
        player.card[rows[row_123]][cols[col_abc]] = "<:crimsoBOT:689896690785976419>"
        player.score += 10 * multiplier
    else:
        player.mismatch_count += 1
        player.score -= player.mismatch_count
        match = False

    # this bool used later to give feedback to user
    return match


async def process_player_response(
    ctx, response: discord.Message, list_of_players: List[Cringo], emojis_already_used: List[str], multiplier: int
) -> bool:
    """Process player response"""
    
    # find player object in list of players; if not a player, then return out of this
    user_object = None
    for player in list_of_players:
        if player.player == response.author:
            user_object = player
            break
    
    if user_object is None:
        return

    # determine if user's reponse is a match
    # matches missed in previous rounds are OK (they only lose the earlier round multiplier)
    positions: List[str] = response.content.replace(".","").strip().split(" ")
    mismatch_detected = False
    for position in positions:
        # if "leave" is detected, end
        if position == "leave":
            embed = await player_remove(list_of_players, user_object)
            await ctx.send(embed=embed)
            return

        # if they're still in the game, then check for matches
        match = await mark_card(user_object, position, emojis_already_used, multiplier)

        if match is False:
            embed = c.crimbed(
                title=None,
                descr="Mismatch(es) detected. You lose points for that!",
                color_name="orange",
            )
            mismatch_detected = True

    # this is after the end of the for loop, so that the mismatch message is sent only once
    if mismatch_detected:
        await response.author.send(embed=embed)

    await response.author.send(await deliver_card(user_object.card))


async def cringo_score(player: Cringo, turn_number: int, multiplier: int) -> None:
    """
    This function checks for and scores complete lines. mark_card() scores individual matches.

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
    n = len(player.card[0])

    def line_score(direction: str, index: Optional[int] = 0) -> bool:
        """Sort through rows or columns to check if all match."""

        # to keep from searching nonexistant rows and columns:
        if index >= n:
            return False
        
        # we skip the header row and column with (1,n)
        for i in range(1, n-1):
            if direction == "row":
                if player.card[index][i] == player.card[index][i+1]:
                    pass
                else:
                    return False
            if direction == "column":
                if player.card[i][index] == player.card[i+1][index]:
                    pass
                else:
                    return False
            if direction == "LR":
                if player.card[i][i] == player.card[i+1][i+1]:
                    pass
                else:
                    return False
            if direction == "RL":
                if player.card[i][n-i] == player.card[i+1][n-(i+1)]:
                    pass
                else:
                    return False

        return True

    # check all rows
    for row in rows:
        if row not in player.lines:
            complete_line = line_score("row", rows[row])
            if complete_line:
                player.lines.add(row)
                player.score += 100 * multiplier

    # then all columns
    for col in cols:
        if col not in player.lines:
            complete_line = line_score("column", cols[col])
            if complete_line:
                player.lines.add(col)
                player.score += 100 * multiplier

    # the two diagonals
    diagonals = ["LR", "RL"]
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
            player.full = True


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

import mmap
import random
from typing import List, Tuple, Union

import discord
from discord import Embed

from crimsobot.models.wordle_results import WordleResults
from crimsobot.utils import tools as c

DiscordUser = Union[discord.User, discord.Member]

# emoji match indicators
no_match = '❌'
in_word = '🟨'
exact_match = '🟩'

# the possible guesses
# https://github.com/tabatkins/wordle-list (Accessed 2022-11-27)
guess_path = c.clib_path_join('games', 'wordle_guesses.txt')

# the possible solutions
# https://static.nytimes.com/newsgraphics/2022/01/25/wordle-solver/assets/solutions.txt (Accessed 2022-11-27)
solution_path = c.clib_path_join('games', 'wordle_solutions.txt')


async def choose_solution() -> str:
    """Choose a random five-letter word from the plaintext file.

    Word lists from New York Times Wordle.

    Approach used: https://stackoverflow.com/a/35579149"""

    line_num = 0
    selected_line = ''

    with open(solution_path, encoding='utf-8', errors='ignore') as f:
        while True:
            line = f.readline()
            if not line:
                break
            line_num += 1
            if random.uniform(0, line_num) < 1:
                selected_line = line

    word = selected_line.strip()

    return word


async def input_checker(user_guess: str) -> bool:
    """Check if the user's input is actually a word.

    Method for checking if input is in text file: https://stackoverflow.com/a/4944929"""

    if len(user_guess) != 5:
        valid = False
    else:
        with open(guess_path, encoding='utf-8', errors='ignore') as f, \
                mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as s:
            if s.find(str.encode(user_guess)) != -1:
                valid = True
            else:
                valid = False

    return valid


async def match_checker(user_guess: str, solution: str) -> Tuple[List[str], str, str]:
    """Check user input against solution"""

    user_matches = [no_match] * 5  # start fresh
    in_solution = ''

    def remove_letter(guess_or_solution: str, index: int, replace_with: str) -> str:
        """Remove a letter to exclude from further matching"""
        temp_list = list(guess_or_solution)  # str to list to make assignment possible
        temp_list[index] = replace_with  # some non-letter symbol
        guess_or_solution = ''.join(temp_list)

        return guess_or_solution

    # check first exclusively for exact matches...
    for idx_in, letter_in in enumerate(user_guess):
        for idx_sol, letter_sol in enumerate(solution):
            if letter_in == letter_sol:
                if idx_in == idx_sol:
                    user_matches[idx_in] = exact_match
                    in_solution += letter_in

                    # remove from both
                    user_guess = remove_letter(user_guess, idx_in, '*')
                    solution = remove_letter(solution, idx_sol, '&')

    # ...then for partial matches
    for idx_in, letter_in in enumerate(user_guess):
        for idx_sol, letter_sol in enumerate(solution):
            if letter_in == letter_sol:
                user_matches[idx_in] = in_word
                in_solution += letter_in

                # remove from both
                user_guess = remove_letter(user_guess, idx_in, '*')
                solution = remove_letter(solution, idx_sol, '&')

    # get a string of letters not in solution
    not_in_solution = user_guess

    for letter in in_solution:
        not_in_solution = not_in_solution.replace(letter, '')

    return user_matches, in_solution, not_in_solution


async def remaining_letters(right_guesses: str, wrong_guesses: str) -> List[str]:
    """Return a list of letters that are still available."""

    alphabet = 'abcdefg\nhijklmn\nopqrstu\nvwxyz'  # line break every 7 chars + padding best for mobile

    remaining_alphabet = []  # list of strings to be represented as emojis

    for letter in alphabet:
        if letter in right_guesses:
            char_to_append = f'[{letter}]'
        elif letter in wrong_guesses:
            char_to_append = ' · '
        elif letter == '\n':
            char_to_append = letter
        else:
            char_to_append = f' {letter} '

        remaining_alphabet.append(char_to_append)

    return remaining_alphabet


async def wordle_stats(discord_user: DiscordUser, guesses: int, word: str) -> None:
    await WordleResults.create_result(discord_user, guesses, word)


async def wordle_stat_embed(user: DiscordUser) -> Embed:
    """Return an embed of a user's Wordle stats"""

    s = await WordleResults.fetch_all_by_user(user)  # type: List[WordleResults]

    plays = len(s)

    if plays == 0:
        embed = c.crimbed(
            title='Sorry—',
            descr="You haven't played any games of WORDLE yet!",
            thumb_name='wordle',
            footer='Play >wordle! You will do this!',
        )
    else:
        guesses_needed = []

        for result in s:
            guesses_needed.append(result.guesses)

        guesses_sans_quits = [x for x in guesses_needed if x != 0]
        quits = guesses_needed.count(0)
        completion_pct = (plays - quits) / plays

        max_guesses = max(guesses_needed)
        min_guesses = min(guesses_sans_quits)
        n_min_guesses = guesses_sans_quits.count(min_guesses)

        mean_guesses = sum(guesses_sans_quits) / len(guesses_sans_quits)

        # time for an ASCII histogram! first, a dict...
        upper_limit = 10
        dictogram = {}
        for ii in range(0, upper_limit):
            key = 'quit' if ii == 0 else str(ii)
            dictogram[key] = guesses_needed.count(ii)

        dictogram[f'{upper_limit}+'] = len([x for x in guesses_needed if x >= 10])

        # get the highest value in the dict by which to scale all the histogram strings
        mode = max(dictogram.values())
        max_dash_length = 12  # chosen for best display on mobile

        histogram_strings = []

        for key, value in dictogram.items():
            # scale each line of dashes
            number_of_dashes = max_dash_length * value / mode
            dashes = '-' * round(number_of_dashes)

            # formatted string for display in embed
            histogram_strings.append(f'{key.rjust(4, " ")}|{str(value).rjust(4, " ")} {dashes}')

        # strings are joined here because f-strings don't get along with backslashes (see field_list)
        histogram_string_list = '\n'.join(histogram_strings)

        embed = c.crimbed(
            title=f'WORDLE stats for {user.name}',
            descr=None,
            thumb_name='wordle',
            footer='Thanks for playing >wordle!',
        )

        ess = '' if n_min_guesses == 1 else 's'

        # list of tuples (name, value) for embed.add_field
        field_list = [
            (
                'Gameplay',
                f'**{plays}** plays, **{quits}** quits (**{completion_pct * 100:.1f}%** completed)',
            ),
            (
                'Most guesses needed',
                f'**{max_guesses}** guesses',
            ),
            (
                'Best solve',
                f'**{min_guesses}** guesses ({n_min_guesses} time{ess})'
            ),
            (
                'Average guesses (sans quits)',
                f'**{mean_guesses:.2f}** guesses'
            ),
            (
                '\u200b',
                f'```{histogram_string_list}```',
            )
        ]

        for field in field_list:
            embed.add_field(name=field[0], value=field[1], inline=False)

    return embed

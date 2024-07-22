import asyncio
import itertools
import random
from typing import List, Optional

import discord
from discord.ext import commands

from config import ADMIN_USER_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.context import CrimsoContext
from crimsobot.data.games import EMOJISTORY_RULES, MADLIBS_RULES, STORIES
from crimsobot.exceptions import NotDirectMessage, StrictInputFailed
from crimsobot.handlers.games import EmojistorySubmissionHandler, EmojistoryVotingHandler
from crimsobot.utils import games as crimsogames, markov as m, tools as c, wordle
from crimsobot.utils.converters import CleanedTextInput
from crimsobot.utils.guess_leaderboard import GuessLeaderboard
from crimsobot.utils.leaderboard import Leaderboard

# crimsoCOIN multiplier for games played in crimsoBOT server
# simple logical checks for ctx.guild.id in in each game below
SERVER_BONUS = 1.15


class Games(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.command(aliases=['madlib'], brief='Multiplayer mad libs! Play solo in DMs.')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def madlibs(self, ctx: commands.Context) -> None:
        """
        Fill in the blanks to make an unexpected story out of a famous copypasta or a snippet of popular literature.
        The bot will take your answer if it starts with the proper prefix.
        """

        prefixes = itertools.cycle(MADLIBS_RULES['prefixes'])

        # first embed
        embed = c.crimbed(
            title="Let's play **MADLIBS!**",
            descr='\n'.join([
                '**Watch out for the prefix: `{0}`, `{1}`, or `{2}`!!!**'.format(*MADLIBS_RULES['prefixes']),
                'This facilitates multiplayer when many people are playing.',
                '•••',
                'Give answers by typing `[prefix] [part of speech]`'
            ]),
        )

        await ctx.send(embed=embed)

        # fetch the story and its terms + other init
        story = random.choice(STORIES)
        needed_terms = story.get_keys()
        color_dict = {key: value for key, value in zip(MADLIBS_RULES['prefixes'], ['green', 'yellow', 'orange'])}
        collected_terms = {}
        authors = []

        # iterate through keys, prompting and listening, rotating thru prefixes
        for prefix, (term, display_as) in zip(prefixes, needed_terms.items()):
            embed = c.crimbed(
                title=f'PREFIX: {prefix}',
                descr=f'I need `{prefix}{display_as}`',
                color_name=color_dict[prefix],
            )

            await ctx.send(embed=embed)

            # check message for author, channel, content
            def check(message: discord.Message) -> bool:
                banned = self.bot.is_banned(message.author)
                has_prefix = message.content.startswith(prefix)  # noqa: B023
                in_channel = message.channel == ctx.message.channel
                return not banned and has_prefix and in_channel

            try:
                message = await self.bot.wait_for('message', check=check, timeout=MADLIBS_RULES['timer'])
            except asyncio.TimeoutError:
                embed = c.crimbed(
                    title='**MADLIBS** has timed out!',
                    descr=None,
                )

                await ctx.send(embed=embed)
                return None

            if message:
                collected_terms[term] = message.content[1:]
                authors.append(message.author.name)

        # tell the story (in embed)
        authors = list(set(authors))
        embed = c.crimbed(
            title=f"{crimsogames.winner_list(authors)}'s madlib!",
            descr=story.text.format(**collected_terms),
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=['cball', 'crimsobot'], brief='Ask crimsoBOT what will be.')
    async def crimsoball(self, ctx: commands.Context, *, question: str) -> None:

        response = crimsogames.get_crimsoball_answer(ctx)
        if response == 'random_response':
            response = await m.crimso(ctx)

        # embed for answer
        embed = c.crimbed(
            title='OH MIGHTY CRIMSOBALL...',
            descr=None,
            thumb_name='8ball',
        )
        embed.add_field(
            name='{} asks:'.format(ctx.message.author),
            value=question,
            inline=False
        )
        embed.add_field(
            name='**crimsoBOT says:**',
            value=response,
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.group(
        aliases=['guess', 'guessemoji'],
        invoke_without_command=True,
        brief='Guess the correct emoji from 2 to 20 choices!')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def guessmoji(self, ctx: commands.Context, n: int) -> None:
        """
        The bot will present 2 to 20 choices, depending on your selection.
        Choose only one; guessing more than once will disqualify you!
        Playing >guess 2 is free. Larger Guessmoji games will cost you.
        Check your >balance! Get game costs and payouts by typing >guesscosts.
        Watch out for the WHAMMY!
        """

        # invalid amount of emojis
        if not 1 <= n <= 20:
            raise commands.BadArgument('Number of emojis is out of bounds.')

        # admins can play guess 1
        if n == 1 and ctx.message.author.id not in ADMIN_USER_IDS:
            raise commands.BadArgument('Number of emojis is out of bounds.')

        # check if user can afford to play!
        winning_amount, cost = crimsogames.guess_economy(n)

        # check if crimsoBOT home server
        if ctx.guild and ctx.guild.id == 552650672965943296:
            winning_amount = winning_amount * SERVER_BONUS

        # the candidates
        choices = [
            '🛐', '😍', '😋', '🐍', '💩', '🌈', '🌖', '🍆', '🐧', '🥚',
            '🍌', '👺', '🧀', '😔', '🦐', '🦀', '🔥', '🍞', '🐸', '🍄'
        ]
        choices = random.sample(choices, n)
        winning_emoji = random.choice(choices)

        # initial message
        # this will be amended as the game progresses
        description = '\n'.join([
            "I'm thinking of an emoji. Can you guess it?",
            "*(Multiple guesses or playing when you can't afford it will disqualify you!)*",
            'The choices are...'
        ])

        embed = c.crimbed(
            title="Let's play **GUESSMOJI!**",
            descr=description,
            footer='Choices: {:1d} · Cost: \u20A2{:.2f} · Payout: \u20A2{:.2f}'.format(n, cost, winning_amount),
        )
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(1.36)

        # add reactions to msg
        for emoji in choices:
            try:
                await msg.add_reaction(emoji)
                await asyncio.sleep(0.36)  # smoother rollout of reactions
            except Exception:
                await ctx.send('**Someone added emojis!** Wait for me to add them, then choose. `Game crashed.`')
                return

        # start timer
        embed.description = description + '\nYou have **eight** seconds. Go!'
        await msg.edit(embed=embed)
        await asyncio.sleep(5)

        embed.description = description + '\n**Three seconds left!**'
        await msg.edit(embed=embed)
        await asyncio.sleep(3)

        # think emoji; processing...
        embed.description = 'pls to hold (rate limits!) The winner is... <a:guessmoji_think:595388191411011615>'
        await msg.edit(embed=embed)

        # initialize winner (will be empty if no one wins)
        # and loser list (may end up as a list of lists, or empty if no one loses)
        winners = []  # type: List[discord.User]
        losers = []  # type: List[discord.User]

        # see who reacted to what
        cache_msg = discord.utils.get(self.bot.cached_messages, id=msg.id)
        for reaction in cache_msg.reactions:
            # get list of users who reacted to each choice
            players = await reaction.users().flatten()

            # remove the banned and poor, but only bother if someone besides the bot reacted
            if len(players) > 1:
                for player in players:
                    is_bot = player.id == self.bot.user.id
                    current_bal = await crimsogames.check_balance(player)
                    cannot_play = self.bot.is_banned(player) or current_bal < (cost if cost != 0 else float('-inf'))
                    # ...this should let people with negative balance play >guess 2

                    if not is_bot and cannot_play:
                        await cache_msg.remove_reaction(reaction.emoji, player)
                        players.remove(player)

                # if winner, get winners; if not, get losers
                if reaction.emoji == winning_emoji:
                    winners = players
                else:
                    losers += players

        # determine if this will be an unfortunate occurance >:)
        whammy = True if random.random() < 0.0036 else False

        if whammy:
            winning_amount = -36  # because funny ooer numner

        if len(losers) != 0:
            # kick out crimsoBOT
            losers = [user for user in losers if user.id != self.bot.user.id]

            # stats + debit the losers
            for user in losers:
                await crimsogames.win(user, (winning_amount if whammy else 0) - cost)
                await crimsogames.guess_luck(user, n, False)

        # kick out crimsoBOT and losers, "flatten" out duplicates
        winners = [user for user in winners if user.id != self.bot.user.id and user not in losers]

        if len(winners) != 0:
            # stats + debit & award crimsoCOIN to winners
            for user in winners:
                await crimsogames.win(user, winning_amount - cost)
                await crimsogames.guess_luck(user, n, True)

            # convert user objects to mentions
            winner_mentions = [user.mention for user in winners]  # List[str]

            # send to helper function for formatting...
            winners_text = crimsogames.winner_list(winner_mentions)

            # ...and change embed description
            embed.description = '...{} guessed it for \u20A2{:.2f}!\nThe answer was {}'.format(
                winners_text, winning_amount, winning_emoji
            )
        else:
            embed.description = '...No one guessed it! The answer was {}'.format(winning_emoji)

        if whammy:
            embed.description = '**WHAMMY!** Everyone loses \u20A2{:.2f} plus the cost of the game!'.format(
                -winning_amount
            )

        # edit msg with result of game
        await msg.edit(embed=embed)

    @commands.command(aliases=['guesscost'])
    async def guesscosts(self, ctx: commands.Context) -> None:
        """Get game costs and payouts for >guess!"""

        costs = crimsogames.guesslist()
        content = '<:crimsoCOIN:588558997238579202> **GUESSMOJI costs and payouts:**```{}```'.format(costs)

        await ctx.send(content)

    @commands.command(brief='Make the best story based on the emojis!')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def emojistory(self, ctx: CrimsoContext) -> None:
        """
        A string of emojis will appear.
        Enter a short story (<300 characters) that corresponds to the emojis, and then vote on the best story!
        The story must begin with $ to be counted.
        The winner gets a chunk of crimsoCOIN proportional the the number of votes cast for their story.

        This game requires the Manage Messages permission.
        """

        emojis = crimsogames.emojistring()

        # first embed: introduction
        embed = c.crimbed(
            title="Let's play **EMOJI STORY!**",
            descr='\n'.join([
                'Invent a short story to go with the following set of emojis.',
                'Begin your story with a dollar sign **$**.',
                'You have {} seconds!'.format(EMOJISTORY_RULES['join_timer']),
                emojis,
            ]),
            thumb_name='random',
        )

        await ctx.send(embed=embed)

        # story listener here
        submission_handler = EmojistorySubmissionHandler(ctx, timeout=EMOJISTORY_RULES['join_timer'])
        submissions = await ctx.gather_events('on_message', handler=submission_handler)

        # strip $ and whitespace from beginning of stories
        for story in submissions.stories:
            story.content = story.content[1:].lstrip(' ')

        # story handler
        voting = False
        if not submissions.stories:
            title = '**EMOJI STORY CANCELLED!**'
            descr = 'No submissions!'
        elif len(submissions.stories) == 1:
            title = '**WINNER BY DEFAULT!**'
            descr = '\n\n'.join([
                'Only one submission by **{}**:'.format(submissions.stories[0].author),
                emojis,
                submissions.stories[0].content,
            ])
        else:
            title = '**VOTE NOW** for the best emoji story!'
            descr = '\n'.join([
                '_ _',
                emojis,
                '_ _',
                '\n'.join(f'{index + 1}. {story.content}' for index, story in enumerate(submissions.stories))
            ])
            voting = True

        # second embed: stories
        embed = c.crimbed(
            title=title,
            descr=descr,
            thumb_name='random'
        )

        await ctx.send(embed=embed)

        # if not voting, end the thing
        if not voting:
            return

        # vote handler
        vote_handler = EmojistoryVotingHandler(ctx, timeout=EMOJISTORY_RULES['vote_timer'])
        vote_handler.set_arguments(stories=submissions.stories)
        ballot = await ctx.gather_events('on_message', handler=vote_handler)

        if not ballot.votes:
            winner = None
            winning_amount = None
            title = '**NO VOTES CAST!**'
            descr = "I'm disappointed."
        else:
            # send to vote counter to get winner
            ind_plus_1, votes_for_winner = crimsogames.tally(ballot.votes)
            winner = submissions.stories[int(ind_plus_1) - 1]
            winning_amount = votes_for_winner * 10.0

            # check if crimsoBOT home server
            if ctx.guild and ctx.guild.id == 552650672965943296:
                winning_amount = winning_amount * SERVER_BONUS

            await crimsogames.win(winner.author, winning_amount)
            s_or_no_s = 's' if votes_for_winner > 1 else ''

            # then the embed info
            title = '**EMOJI STORY WINNER!**'
            descr = '\n\n'.join([
                f'The winner is **{winner.author}** with {votes_for_winner} vote{s_or_no_s} for their story:',
                emojis,
                winner.content,
            ])

        # final embed: results!
        embed = c.crimbed(
            title=title,
            descr=descr,
            thumb_name='random',
            footer=f'{winner.author} gets {winning_amount} crimsoCOIN!' if winner else None,
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=['bal'])
    async def balance(self, ctx: commands.Context, whose: Optional[discord.Member] = None) -> None:
        """Check your or someone else's crimsoCOIN balance."""

        if not whose:
            whose = ctx.message.author

        encourage = [
            'Nice!',
            'Way to go!',
            "Let's get that bread!",
            'Buy crimso some ice cream.',
            'cash money',
            "You're the best!",
            "Dinner's on you tonight!",
            "It's worth nothing!"
        ]

        bal = await crimsogames.check_balance(whose)

        embed = c.crimbed(
            title=f'\u200B\n{whose} has **\u20A2{bal:.2f}**.',
            descr=random.choice(encourage) if bal > 0 else '=[',
            thumb_name='crimsoCOIN',
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=['pay'])
    @commands.cooldown(2, 60*30, commands.BucketType.user)
    async def give(self, ctx: commands.Context, recipient: discord.Member, amount: float) -> None:
        """Give a user up to 1/4 of your crimsoCOIN."""

        # firstly, round amount
        amount = round(amount, 2)

        # no negative values & make sure they can afford it
        if amount <= 0:
            raise commands.BadArgument('Amount less than 0.')
        elif amount > await crimsogames.check_balance(ctx.message.author) * 0.25:
            embed = c.crimbed(
                title=f'\u200B\n{ctx.message.author}, you cannot give more than 1/4 of your balance!',
                descr='Check your `>balance`.',
                thumb_name='crimsoCOIN',
            )
            await ctx.send(embed=embed)
            return

        if self.bot.is_banned(recipient):
            return

        # transaction
        await crimsogames.win(ctx.message.author, -amount)  # credit
        await crimsogames.win(recipient, amount)  # debit

        # message (embed)
        encourage = [
            'Nice!',
            'How sweet! =]',
            '*sucker*',
            "Give crimso some while you're at it.",
            'Your money... is GONE!',
            "You're the best!",
            'Oooh big spender'
        ]

        embed = c.crimbed(
            title='\u200B\n{} has given {} **\u20A2{:.2f}** crimsoCOIN.'.format(ctx.message.author, recipient, amount),
            descr=random.choice(encourage),
            thumb_name='crimsoCOIN',
        )

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def cgive(self, ctx: commands.Context, recipient: discord.Member, amount: float) -> None:
        """Manual adjustment of crimsoCOIN values."""

        # change to float
        amount = float(amount)

        await crimsogames.win(recipient, amount)  # debit
        embed = c.crimbed(
            title="\u200B\n{} has adjusted {}'s balance by {neg}\u20A2**{:.2f}**.".format(
                ctx.message.author, recipient, abs(amount), neg='-' if amount < 0 else ''
            ),
            descr='Life is inherently unfair.' if amount < 0 else 'Rejoice in your good fortune!',
            thumb_name='crimsoCOIN',
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=['lb'])
    async def leaderboard(self, ctx: commands.Context, page: int = 1) -> None:
        """Overall crimsoCOIN winnings leaderboard."""

        lb = Leaderboard(page)
        await lb.get_coin_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @commands.command(aliases=['luck', 'gstats'])
    async def guessstats(self, ctx: commands.Context, whose: Optional[discord.Member] = None) -> None:
        """Check your or someone else's GUESSMOJI! stats!"""

        if not whose:
            whose = ctx.message.author

        embed = await crimsogames.guess_stat_embed(whose)
        await ctx.send(embed=embed)

    @guessmoji.group(name='lb', aliases=['glb'], invoke_without_command=True)
    async def guess_lb(self, ctx: commands.Context) -> None:
        """GUESSMOJI! leaderboards"""

        # Fallback to luck leaderboard if no command is provided
        await self.glb_luck.invoke(ctx)

    @guess_lb.command(name='luck')
    async def glb_luck(self, ctx: commands.Context, page: int = 1) -> None:
        """GUESSMOJI! luck leaderboard."""

        lb = GuessLeaderboard(page)
        await lb.get_luck_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @guess_lb.command(name='plays')
    async def glb_plays(self, ctx: commands.Context, page: int = 1) -> None:
        """GUESSMOJI! plays leaderboard"""

        lb = GuessLeaderboard(page)
        await lb.get_plays_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @commands.command()
    async def daily(self, ctx: commands.Context, lucky_number: int) -> None:
        """Get a daily award! Pick a number 1-100 for a chance to win bigger!"""

        # exception handling
        if not 1 <= lucky_number <= 100:
            raise commands.BadArgument('Lucky number is out of bounds.')

        # pass to helper and spit out result in an embed
        embed = await crimsogames.daily(ctx.message.author, lucky_number)

        await ctx.send(embed=embed)

    @commands.command(aliases=['bw'])
    @commands.cooldown(5, 30, commands.BucketType.channel)
    async def bubblewrap(
        self,
        ctx: commands.Context,
        *,
        bubble: CleanedTextInput = None  # type: ignore
    ) -> None:
        """Get a little sheet of bubble wrap to pop!
        Provide any standard emoji or custom emoji to pop!
        If you use the command by itself, get a random emoji!
        Short text inputs can also be used.

        There is a per-channel cooldown on this command."""

        def choose_random_emoji() -> str:
            """Choose a random emoji from the emojis used in Emojistory."""
            with open(c.clib_path_join('games', 'emojilist.txt'), encoding='utf8', errors='ignore') as emoji_file:
                return random.choice(''.join(emoji_file.readlines()).strip('\n'))

        # configure
        size = 6

        # If bubble is None, there was simply no input.
        if bubble is None:
            bubble = choose_random_emoji()  # type: ignore

        # However, if bubble is false-y (and not None) conversion failed - error.
        if not bubble:
            raise StrictInputFailed

        # build the bubblewrap sheet and send
        line = '\u200B\n' + size * f'\u200b||{bubble}||'
        sheet = size * line

        await ctx.send(sheet)

    @commands.command(aliases=['w'])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def wordle(self, ctx: commands.Context) -> None:
        """Play a Wordle clone in your DMs!"""

        # check if direct message
        not_dm = ctx.message.channel.type != discord.ChannelType.private
        if not_dm:
            raise NotDirectMessage

        # tracking variables
        matches_history = []  # list of strings
        matched_letters = ''
        missed_letters = ''

        solution = await wordle.choose_solution()

        # welcome message
        embed = c.crimbed(
            title="Let's play **WORDLE!**",
            descr='\n'.join([
                'Try to guess the five-letter word!',
                'Begin your guess with a period like this: `.bread`',
                'Letter is somewhere in word: 🟨',
                'Letter is in the correct spot: 🟩',
                'To end the game, type `.quit`',
            ]),
            footer='Gameplay is unlimited; you have to either win or ".quit"!',
            thumb_name='wordle',
        )

        await ctx.send(embed=embed)
        await asyncio.sleep(1.2)

        # check message for author, channel, content
        def check(message: discord.Message) -> bool:
            banned = self.bot.is_banned(message.author)
            has_prefix = message.content.startswith('.')
            in_channel = message.channel == ctx.message.channel
            return not banned and has_prefix and in_channel

        # user input loop
        solved = False
        turns_taken = 0

        # begin game embed
        embed = c.crimbed(
            title='**HERE WE GO!**',
            descr='Start guessing!',
        )

        await ctx.send(embed=embed)

        while not solved:
            input_valid = False
            while input_valid is False:
                # get user input
                message = await self.bot.wait_for('message', check=check)
                user_input = message.content[1:].lower().strip()
                if user_input == 'quit':
                    turns_taken = 0  # set turns to 0 (0 = quit in DB)
                    embed = c.crimbed(
                        title='**OOF!**',
                        descr=f'The word was **{solution}**!',
                        footer='Better luck next time!',
                        color_name='orange',
                        thumb_name='weary',
                    )

                    await ctx.send(embed=embed)

                    # store stats
                    await wordle.wordle_stats(ctx.message.author, turns_taken, solution)

                    return  # game over, end function

                input_valid = await wordle.input_checker(user_input)

                if not input_valid:
                    embed = c.crimbed(
                        title=None,
                        descr='Your guess is not in the word list.',
                        color_name='yellow',
                    )

                    await ctx.send(embed=embed)

            match_emojis, matches, misses = await wordle.match_checker(user_input, solution)
            turns_taken += 1

            # make the emoji string to graph guesses
            match_emoji_str = ''.join(match_emojis)

            # check if solved
            solved = user_input == solution

            # add results to tracking variables
            matches_history.append(f'{match_emoji_str} - `{user_input}`')
            matched_letters += matches
            missed_letters += misses

            if not solved:
                remaining = await wordle.remaining_letters(matched_letters, missed_letters)
                embed = c.crimbed(
                    title=f'Guess #{turns_taken}: **{user_input}**',
                    descr='\n'.join([
                        '\n'.join(matches_history),
                        '',
                        '**LETTERS**',
                        f'`{"".join(remaining)}`',
                    ]),
                    thumb_name='think'
                )

                await ctx.send(embed=embed)

        # store stats
        await wordle.wordle_stats(ctx.message.author, turns_taken, solution)

        # award coin
        base_prize = 2.25
        winnings = base_prize * (2 ** (6 - turns_taken)) if turns_taken < 6 else base_prize
        await crimsogames.win(ctx.message.author, winnings)

        # print results on solve
        embed = c.crimbed(
            title='**WINNER!**',
            descr='\n'.join(matches_history),
            footer=f'{turns_taken} guesses · \u20A2{winnings:.2f} won!',
            thumb_name='party',
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=['wstats'])
    async def wordlestats(self, ctx: commands.Context) -> None:
        """Check your Wordle stats!"""

        embed = await wordle.wordle_stat_embed(ctx.message.author)
        await ctx.send(embed=embed)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Games(bot))

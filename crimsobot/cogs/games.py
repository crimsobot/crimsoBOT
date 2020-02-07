import asyncio
import random
import time
from typing import List, Optional

import discord
from discord.ext import commands

from config import ADMIN_USER_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.utils import checks, games as crimsogames, tools as c
from crimsobot.utils.leaderboard import Leaderboard

# lists for games in progress
madlibs_channels = []  # type: List[int]
guess_channels = []  # type: List[int]
emojistory_channels = []  # type: List[int]
cringo_channels = []

class Games(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.command(aliases=['madlib'], brief='Multiplayer mad libs! Play solo in DMs.')
    async def madlibs(self, ctx: commands.Context) -> None:
        """
        Fill in the blanks to make an unexpected story out of a famous copypasta or a snippet of popular literature.
        The bot will take your answer if it starts with the proper prefix.
        """

        chk = c.checkin('madlibs', ctx.message.guild, ctx.message.channel, madlibs_channels)
        if chk is False:
            raise commands.errors.CommandInvokeError('In list')

        prefix = ['&', '*', '%']

        # first embed
        title = "Let's play **MADLIBS!**"
        descr = (
                '**Watch out for the prefix: `{0}`, `{1}`, or `{2}`!!!**\n'.format(*prefix) +
                'This facilitates multiplayer when many people are playing.\n'
                '•••\n'
                'Give answers by typing `[prefix] [part of speech]`\n'
        )
        embed = c.crimbed(title, descr)
        await ctx.send(embed=embed)

        # fetch the story and its keys
        story = crimsogames.get_story()
        keys = crimsogames.get_keys(story)

        # shuffle to make less obvious which story it is
        random.shuffle(keys)

        # iterate through keys, prompting and listening, w/ alternating prefix
        counter = 0
        authors = []  # list of authors
        for key in keys:
            counter += 1
            p = prefix[counter % len(prefix)]
            if key.startswith('#'):
                embed = c.crimbed('PREFIX: ' + p, 'I need `{}{}`'.format(p, key[1:]))
            else:
                embed = c.crimbed('PREFIX: ' + p, 'I need `{}{}`'.format(p, key))
            await ctx.send(embed=embed)

            # check message for author, channel, content
            def check(msg: discord.Message) -> bool:
                banned = self.bot.is_banned(msg.author)
                has_prefix = msg.content.startswith(p)
                in_channel = msg.channel == ctx.message.channel

                return not banned and has_prefix and in_channel

            # return term if message passes check
            term = await self.bot.wait_for('message', check=check)

            # end game if timeout
            if term is None:
                embed = c.crimbed('**MADLIBS** has timed out!', None)
                await ctx.send(embed=embed)

                c.checkout('madlibs', ctx.message.guild, ctx.message.channel, madlibs_channels)

                return

            # update ALL (if linked) or just first instance with term
            if key.startswith('#'):
                story = story.replace('{' + key + '}', term.content[1:])
            else:
                story = story.replace('{' + key + '}', term.content[1:], 1)

            # add author of term to list
            authors.append(term.author.name)

        # tell the story (in embed)
        authors = list(set(authors))
        authors_ = crimsogames.winner_list(authors)
        embed = c.crimbed("{}'s madlib!".format(authors_), story)
        await ctx.send(embed=embed)

        # if channel, remove channel from list
        c.checkout('madlibs', ctx.message.guild, ctx.message.channel, madlibs_channels)

    @commands.command(aliases=['cball', 'crimsobot'], brief='Ask crimsoBOT what will be.')
    async def crimsoball(self, ctx: commands.Context, *, question: str) -> None:
        # list of answers (which I need to store somewhere besides in the function)
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
            "is the sky blue?\n\nis it? i don't know. i don't have eyes.",
            "i can't be bothered with this right now.",
            'funny you should ask--',
            'fine, sure, whatever',
            '<:xok:551174281367650356>',
            'ask seannerz. ping him now and ask.',
            'ehhhh sure',
            'hmmmm. no.',
            'uhhhhhhhhh',
            '<:uhhhh:495249068789071882>',
            'eat glass!'
        ]

        # embed for answer
        title = '**OH MIGHTY CRIMSOBALL...**'
        quest = '{} asks:\n{}'.format(ctx.message.author, question)
        answer = '**crimsoBOT says**: {}'.format(random.choice(answer_list))
        thumb = 'https://i.imgur.com/6dzqq78.png'  # 8-ball
        embed = c.crimbed(title, quest + '\n\n' + answer, thumb)

        await ctx.send(embed=embed)

    @commands.command(aliases=['guess', 'guessemoji'], brief='Guess the correct emoji from 2 to 20 choices!')
    @commands.cooldown(2, 10, commands.BucketType.user)
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

        # the candidates
        choices = [
            '🛐', '😍', '😋', '🐍', '💩', '🌈', '🌖', '🍆', '🐧', '🥚',
            '🍌', '👺', '🧀', '😔', '🦐', '🦀', '🔥', '🍞', '🐸', '🍄'
        ]
        choices = random.sample(choices, n)
        winning_emoji = random.choice(choices)

        # check if running in channel
        chk = c.checkin('guessemoji', ctx.message.guild, ctx.message.channel, guess_channels)
        if chk is False:
            raise commands.errors.CommandInvokeError(chk)

        # initial message
        title = "Let's play **GUESSMOJI!**"
        description = """
        I'm thinking of an emoji. Can you guess it?
        *(Multiple guesses or playing when you can't afford it will disqualify you!)*
        The choices are...
        """
        thumb = None  # https://i.imgur.com/zJtRYNJ.jpg
        footer = 'Choices: {:1d} · Cost: \u20A2{:.2f} · Payout: \u20A2{:.2f}'.format(n, cost, winning_amount)

        embed = c.crimbed(title, description, thumb)
        embed.set_footer(text=footer)
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(1.36)

        # add reactions to msg
        for emoji in choices:
            try:
                await msg.add_reaction(emoji)
                await asyncio.sleep(0.36)  # smoother rollout of reactions
            except Exception:
                c.checkout('guessemoji', ctx.message.guild, ctx.message.channel, guess_channels)
                await ctx.send('**Someone added emojis!** Wait for me to add them, then choose. `Game crashed.`')

                return

        # start timer
        embed.description = description + 'You have **eight** seconds. Go!'
        await msg.edit(embed=embed)
        await asyncio.sleep(5)

        embed.description = description + '**Three seconds left!**'
        await msg.edit(embed=embed)
        await asyncio.sleep(3)

        # remove channel from list; allow gameplay again instantly
        c.checkout('guessemoji', ctx.message.guild, ctx.message.channel, guess_channels)

        # think emoji; processing...
        embed.description = '...<a:guessmoji_think:595388191411011615>'
        await msg.edit(embed=embed)

        # initialize winner (will be empty if no one wins)
        # and loser list (may end up as a list of lists, or empty if no one loses)
        winners = []  # type: List[discord.User]
        losers = []  # type: List[discord.User]

        # see who reacted to what
        cache_msg = discord.utils.get(self.bot.cached_messages, id=msg.id)
        for reaction in cache_msg.reactions:
            # remove the banned and poor...
            players = await reaction.users().flatten()

            # ...but only bother with this shit if someone besides the bot reacted
            if len(players) > 1:
                for player in players:
                    is_bot = player.id == self.bot.user.id
                    cannot_play = self.bot.is_banned(player) or \
                        await crimsogames.check_balance(player) < (cost if cost != 0 else float('-inf')) 
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
            winning_amount = -36 # because funny ooer numner

        if len(losers) != 0:
            # kick out crimsoBOT
            losers = [user for user in losers if user.id != self.bot.user.id]

            # stats + debit the losers
            for user in losers:
                await crimsogames.win(user, (winning_amount if whammy else 0) - cost)
                await crimsogames.guess_luck(user, n, False)

        if len(winners) != 0:
            # kick out crimsoBOT and losers
            winners = [user for user in winners if user.id != self.bot.user.id and user not in losers]

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
            embed.description = '**WHAMMY!** Everyone loses -\u20A2{:.2f} plus the cost of the game!'.format(
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
    async def emojistory(self, ctx: commands.Context) -> None:
        """
        A string of emojis will appear.
        Enter a short story (<250 characters) that corresponds to the emojis, and then vote on the best story!
        The story must begin with $ to be counted.
        The winner gets a chunk of crimsoCOIN proportional the the number of votes cast for their story.

        This game requires the Manage Messages permission.
        """

        # check if running in channel
        chk = c.checkin('emojistory', ctx.message.guild, ctx.message.channel, emojistory_channels)
        if chk is False:
            raise commands.errors.CommandInvokeError('Channel in list')

        # first embed: introduction
        timer = 63  # seconds
        intro = """
        Invent a short story to go with the following set of emojis.
        Begin your story with a dollar sign **$**.
        You have {} seconds!
        """.format(timer)

        emojis = crimsogames.emojistring()
        thumbs = [
            'https://i.imgur.com/bBXRFnO.png',  # triumph
            'https://i.imgur.com/8deo8Ak.png',  # joy
            'https://i.imgur.com/lSPKbWf.png',  # hug
            'https://i.imgur.com/odD9yI2.png',  # think
            'https://i.imgur.com/sppk4te.png',  # scared
            'https://i.imgur.com/VFtApPg.png',  # weary
            'https://i.imgur.com/lNR8qHe.png',  # money mouth
        ]
        thumb = random.choice(thumbs)
        embed = c.crimbed("Let's play **EMOJI STORY!**", intro + emojis, thumb)
        await ctx.send(embed=embed)

        # define check for prefix, channel, and if author has already submitted
        def story_check(msg: discord.Message) -> bool:
            banned = self.bot.is_banned(msg.author)
            has_prefix = msg.content.startswith('$')
            just_right = 5 < len(msg.content) < 250
            in_channel = msg.channel == ctx.message.channel
            is_author = msg.author in authors
            return not banned and has_prefix and just_right and in_channel and not is_author

        # initialize story listener
        stories = []
        authors = []
        end = time.time() + timer
        while time.time() < end:
            try:
                story = await self.bot.wait_for('message', check=story_check, timeout=0.5)
            except asyncio.TimeoutError:
                continue

            if story is not None:
                stories.append(story)
                authors.append(story.author)
                await story.delete()

        # strip $ and whitespace from beginning of stories
        for story in stories:
            story.content = story.content[1:].lstrip(' ')

        # story handler
        voting = False
        if len(stories) == 0:
            title = '**EMOJI STORY CANCELLED!**'
            descr = 'No submissions!'
        elif len(stories) == 1:
            title = '**WINNER BY DEFAULT!**'
            descr = 'Only one submission by **{x.author}**:\n\n{e}\n\n{x.content}'.format(x=stories[0], e=emojis)
        else:
            title = '**VOTE NOW** for the best emoji story!'
            descr = '_ _\n' + emojis + '\n\n' + '\n'.join(
                str(stories.index(story) + 1) + '. {story.content}'.format(story=story) for story in stories
            )
            voting = True

        # second embed: stories
        embed = c.crimbed(title, descr, thumb)
        await ctx.send(embed=embed)

        # if not voting, end the thing
        if voting is False:
            c.checkout('emojistory', ctx.message.guild, ctx.message.channel, emojistory_channels)
            return

        # define check for prefix, channel, and if author has already submitted
        def vote_check(msg: discord.Message) -> bool:
            try:
                banned = self.bot.is_banned(msg.author)
                in_channel = msg.channel == ctx.message.channel
                valid_choice = 0 < int(msg.content) <= len(stories)
                has_voted = msg.author in voters
                return not banned and valid_choice and in_channel and not has_voted
            except ValueError:
                return False

        # initialize voting listener
        votes = []
        voters = []
        end_voting = time.time() + 45
        while time.time() < end_voting:
            try:
                vote = await self.bot.wait_for('message', check=vote_check, timeout=0.5)
            except asyncio.TimeoutError:
                continue

            if vote is not None:
                votes.append(vote.content)
                voters.append(vote.author)
                await vote.delete()
                embed = c.crimbed(None, '**{}** voted.'.format(vote.author), None)
                user_has_voted_message = await ctx.send(embed=embed)
                await user_has_voted_message.delete(delay=8)

        # vote handler
        if len(votes) == 0:
            winner = None
            title = '**NO VOTES CAST!**'
            descr = "I'm disappointed."
        else:
            # send to vote counter to get winner
            ind_plus_1, votes_for_winner = crimsogames.tally(votes)
            winner = stories[int(ind_plus_1) - 1]
            winning_amount = votes_for_winner * 10
            await crimsogames.win(winner.author, winning_amount)
            ess = 's' if votes_for_winner > 1 else ''

            # then the embed info
            title = '**EMOJI STORY WINNER!**'
            descr = 'The winner is **{x.author}** with {y} vote{s} for their story:\n\n{e}\n\n{x.content}'.format(
                x=winner, y=votes_for_winner, s=ess, e=emojis)

        # third embed: results!
        embed = c.crimbed(title, descr, thumb)
        if winner:
            embed.set_footer(text='{} gets {} crimsoCOIN!'.format(winner.author, winning_amount))

        await ctx.send(embed=embed)

        c.checkout('emojistory', ctx.message.guild, ctx.message.channel, emojistory_channels)

    @commands.command(aliases=['bingo'], brief='A quirky take on bingo.')
    # @commands.max_concurrency(1, commands.BucketType.channel)
    async def cringo(self, ctx: commands.Context) -> None:
        """
        A peculiar blend of slots and bingo that is totally not a ripoff of a popular 1990s PC game.
        Points are awarded for matches, completing lines, and getting a full house.
        The earlier you get a match or a line, the more points you get!
        The winners are awarded a handsome amount of crimsoCOIN.
        """

        # check if running in channel
        chk = c.checkin('cringo', ctx.message.guild, ctx.message.channel, cringo_channels)
        if chk is False:
            raise commands.errors.CommandInvokeError('Channel in list')

        # generate game intro embed
        join_timer = 45
        embed = c.crimbed(
            title = "Let's play **CRINGO!**",
            description = """
            Type `$join` to join this game. You have {} seconds!
            Your CRINGO! card will be DMed to you.
            The emojis will be called in your DM.
            """.format(join_timer),
            thumbnail = 'https://i.imgur.com/gpRToBn.png'  # jester
        )
        await ctx.send(embed=embed)

        def pchk(name:str, var) -> None:
            print("{} = {}".format(name, var))

        # solicit players to join the game
        # define check
        def join_cringo(msg: discord.Message) -> bool:
            banned = self.bot.is_banned(msg.author)
            asks_to_join = msg.content.startswith('$join')
            in_channel = msg.channel == ctx.message.channel
            already_joined = msg.author in users_already_joined
            return not banned and asks_to_join and in_channel and not already_joined

        # initialize join-message listener
        users_already_joined = []
        end = time.time() + join_timer
        while time.time() < end:
            try:
                join_request = await self.bot.wait_for('message', check=join_cringo, timeout=10)
                # PCHK, REMOVE
                pchk('join_request.author', join_request.author)

            except asyncio.TimeoutError:
                continue
            
            if join_request is not None:
                # send instructions; if they can't receive DMs, they can't play
                try:
                    potential_player = join_request.author
                    embed = c.crimbed(
                        title = "Welcome to **CRINGO!**",
                        description = """
                            Match the emojis called to the emojis on your card.
                            If you see a match, type the column and row of the match!
                            For example, type ".b4" or ". a1" here. Spaces don't matter.
                            Check your score in between turns in the channel. Good luck!
                            """,
                        thumbnail = 'https://i.imgur.com/gpRToBn.png'  # jester
                    )
                    await potential_player.send(embed=embed)
                    users_already_joined.append(join_request.author)
                    embed = c.crimbed(
                        None,
                        '**{}** has joined the game!'.format(join_request.author),
                        None
                    )
                    await ctx.send(embed=embed)
                    await join_request.delete()
                except discord.errors.Forbidden:
                    embed = c.crimbed(
                        title = None,
                        description = 'Uh oh, **{} CANNOT** join the game!'.format(join_request.author),
                        footer = """
                            You can't call cringo from a DM!
                            You have to be able to receive DMs from crimsoBOT to play!
                            """
                    )
                    await ctx.send(embed=embed)
                    c.checkout('cringo', ctx.message.guild, join_request.author, cringo_players)
                    await join_request.delete()
        
        # if no one joins, end game
        if len(users_already_joined) == 0:
            embed = c.crimbed(title = None, description = 'No one joined! Game cancelled.')
            await ctx.send(embed=embed)
            return
        
        # here's a super-basic class that's not in the right place!
        class Cringo:
            def __init__(self, player, card, score, matches):
                self.player = player
                self.card = card
                self.score = score
                self.matches = matches
        
        # initialize player objects, send everyone their card
        list_of_players  = []
        for player in users_already_joined:
            card = crimsogames.cringo_card(crimsogames.cringo_emoji(4))
            player_object = Cringo(player, card, 0, set())
            list_of_players.append(player_object)
            await player.send(crimsogames.deliver_card(player_object.card))
        
        # initial game variables
        turn_timer = 30
        turn = 1
        total_turns = 9
        game_on = True
        emojis_already_used = [] # should i columnize this?

        # define check
        def player_response(msg: discord.Message) -> bool:
            begins_with_period = msg.content.startswith('.')
            is_a_player = msg.author in users_already_joined
            is_DM = isinstance(msg.channel, discord.DMChannel)
            return begins_with_period and is_a_player and is_DM

        while game_on:
            # display initial leaderboard
            embed = c.crimbed(
                title = "**CRINGO!** scoreboard",
                description = await crimsogames.cringo_leaderboard(list_of_players),
                footer = "Turn #{} coming up!".format(turn)
            )
            await ctx.send(embed=embed)

            await asyncio.sleep(10)

            # choose emojis, send to channel
            emojis_this_turn = crimsogames.cringo_emoji(1, emojis_already_used)
            emojis_already_used.extend(emojis_this_turn[0])
            multiplier = total_turns + 1 - turn

            # send out the emojis for this turn
            embed = c.crimbed(
                title = "**CRINGO!** Turn #{}".format(turn),
                description = ' '.join(emojis_this_turn[0]),
                footer = "{}x multiplier · {} seconds!".format(multiplier, turn_timer)
            )
            # await ctx.send(embed=embed)

            for player in list_of_players:
                await player.player.send(embed=embed)

            # set up listener for players scoring their cards
            turn_end = time.time() + turn_timer
            while time.time() < turn_end:
                try:
                    pchk('response_timeout', True)
                    response = await self.bot.wait_for('message', check=player_response, timeout=10)
                    # PCHK, REMOVE
                    pchk('response.author', response.author)

                except asyncio.TimeoutError:
                    continue

                if response is not None:
                    # find player's card
                    for player in list_of_players:
                        if player.player == response.author:
                            user_object = player
                            break
                    
                    # determine if user's reponse is a match
                    match = crimsogames.mark_card(user_object.card, response.content, emojis_this_turn)
                    if match:
                        # each match gives points
                        user_object.score += 10 * multiplier
                        await response.author.send(crimsogames.deliver_card(user_object.card))
                    else:
                        user_object.score -= 10
                        await response.author.send("`Not a match! You lose 10 points.`")

            # end of turn, time to score matches
            for player in list_of_players:
                crimsogames.cringo_score(player, turn, multiplier)

            # time's up message to each user
            for player in list_of_players:
                await player.player.send("`Time's up!`")

            turn += 1
            if turn > total_turns:
                for player in list_of_players:
                    await player.player.send("`Good game!`")
                game_on = False
        
        # Final score!
        nerf = 50 # (points / nerf = coin)
        embed = c.crimbed(
            title = "**CRINGO!** FINAL SCORE",
            description = await crimsogames.cringo_leaderboard(list_of_players, True, nerf),
            footer = 'Your points/10 = your crimsoCOIN winnings!',
            thumbnail = 'https://i.imgur.com/gpRToBn.png'  # jester
        )
        await ctx.send(embed=embed)
        
        c.checkout('cringo', ctx.message.guild, ctx.message.channel, cringo_channels)

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

        title = '\u200B\n{} has **\u20A2{:.2f}**.'.format(whose, bal)
        descr = random.choice(encourage) if bal > 0 else '=['
        thumb = 'https://i.imgur.com/rS2ec5d.png'
        embed = c.crimbed(title, descr, thumb)

        await ctx.send(embed=embed)

    @commands.command(aliases=['luck'])
    async def luckindex(self, ctx: commands.Context, whose: Optional[discord.Member] = None) -> None:
        """Check your or someone else's luck at Guessmoji!"""

        if not whose:
            whose = ctx.message.author

        luck, plays = await crimsogames.guess_luck_balance(whose)

        title = '\u200B\n{} has a **{:.3f}** luck index on {} plays.'.format(whose, 100 * luck, plays)
        descr = '*Luck tracking as of 01 July 2019.*'
        thumb = 'https://i.imgur.com/rS2ec5d.png'
        embed = c.crimbed(title, descr, thumb)
        embed.set_footer(text='100 is expected · >100 means better luck · <100 means worse luck')

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(2, 1 * 60 * 60, commands.BucketType.user)
    async def give(self, ctx: commands.Context, recipient: discord.Member, amount: float) -> None:
        """Give a user up to 1/10 of your crimsoCOIN."""

        # thumbnail
        thumb = 'https://i.imgur.com/rS2ec5d.png'

        # firstly, round amount
        amount = round(amount, 2)

        # no negative values
        if amount <= 0:
            raise commands.BadArgument('Amount less than 0.')
        # not if exceeds balance
        elif amount > await crimsogames.check_balance(ctx.message.author) * 0.25:
            title = '\u200B\n{}, you cannot give more than 1/4 of your balance!'.format(ctx.message.author)
            descr = 'Check your `>balance`.'
            embed = c.crimbed(title, descr, thumb)
            await ctx.send(embed=embed)
            return
        else:
            pass

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

        title = '\u200B\n{} has given {} **\u20A2{:.2f}** crimsoCOIN.'.format(ctx.message.author, recipient, amount)
        descr = random.choice(encourage)
        embed = c.crimbed(title, descr, thumb)

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @checks.is_admin()
    async def cgive(self, ctx: commands.Context, recipient: discord.Member, amount: float) -> None:
        """Manual adjustment of crimsoCOIN values."""

        # change to float
        amount = float(amount)

        await crimsogames.win(recipient, amount)  # debit
        title = "\u200B\n{} has adjusted {}'s balance by {neg}\u20A2**{:.2f}**.".format(
            ctx.message.author, recipient, abs(amount), neg='-' if amount < 0 else ''
        )
        descr = 'Life is inherently unfair.' if amount < 0 else 'Rejoice in your good fortune!'
        thumb = 'https://i.imgur.com/rS2ec5d.png'
        embed = c.crimbed(title, descr, thumb)

        await ctx.send(embed=embed)

    @commands.group(aliases=['leaders', 'lb'], invoke_without_command=True)
    async def leaderboard(self, ctx: commands.Context) -> None:
        """crimsoCOIN leaderboard!"""

        # Fallback to coin leaderboard if no command is provided, retains prior functionality
        await self.leaderboard_coin.invoke(ctx)

    @leaderboard.command(name='coin')
    async def leaderboard_coin(self, ctx: commands.Context, page: int = 1) -> None:
        """crimsoCOIN leaderboard: COIN!"""

        lb = Leaderboard(page)
        await lb.get_coin_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @leaderboard.command(name='luck')
    async def leaderboard_luck(self, ctx: commands.Context, page: int = 1) -> None:
        """crimsoCOIN leaderboard: LUCK!"""

        lb = Leaderboard(page)
        await lb.get_luck_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @leaderboard.command(name='plays')
    async def leaderboard_plays(self, ctx: commands.Context, page: int = 1) -> None:
        """crimsoCOIN leaderboard: PLAYS!"""

        lb = Leaderboard(page)
        await lb.get_plays_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def daily(self, ctx: commands.Context, lucky_number: int = 0) -> None:
        """Get a daily award! Pick a number 1-100 for a chance to win bigger!"""

        # exception handling
        if not 0 <= lucky_number <= 100:
            raise commands.BadArgument('Lucky number is out of bounds.')

        # pass to helper and spit out result in an embed
        result_string = await crimsogames.daily(ctx.message.author, lucky_number)
        embed = c.crimbed(None, result_string, None)

        await ctx.send(embed=embed)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Games(bot))

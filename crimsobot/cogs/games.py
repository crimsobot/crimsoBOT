import asyncio
import random
import time
from typing import List, Optional

import discord

from discord import Embed

from discord.ext import commands

from config import ADMIN_USER_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.utils import games as crimsogames, tools as c
from crimsobot.utils.leaderboard import Leaderboard


# crimsoCOIN multiplier for games played in crimsoBOT server
# simple logical checks for ctx.guild.id in in each game below
server_bonus = 1.15


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

        prefix = ['&', '*', '%']

        # first embed
        embed = c.crimbed(
            title="Let's play **MADLIBS!**",
            descr="\n".join([
                "**Watch out for the prefix: `{0}`, `{1}`, or `{2}`!!!**".format(*prefix),
                "This facilitates multiplayer when many people are playing.",
                "•••",
                "Give answers by typing `[prefix] [part of speech]`"
            ]),
        )
        await ctx.send(embed=embed)

        # fetch the story and its keys
        story = crimsogames.get_story()
        keys = crimsogames.get_keys(story)

        # shuffle to make less obvious which story it is
        random.shuffle(keys)

        # initialize
        counter = 0
        list_of_authors = []  # list of authors
        # iterate through keys, prompting and listening, rotating thru prefixes
        for key in keys:
            counter += 1
            p = prefix[counter % len(prefix)]
            # if a key begins with #, it's meant to be repeated throughout the story
            # but the "#" needs to be removed, ergo:
            key_to_print = key
            if key.startswith('#'):
                key_to_print = key[1:]

            embed = c.crimbed(
                title="PREFIX: {}".format(p),
                descr='I need `{}{}`'.format(p, key_to_print),
            )
            await ctx.send(embed=embed)

            # check message for author, channel, content
            def check(msg: discord.Message) -> bool:
                banned = self.bot.is_banned(msg.author)
                has_prefix = msg.content.startswith(p)
                in_channel = msg.channel == ctx.message.channel
                return not banned and has_prefix and in_channel

            try:
                term = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                embed = c.crimbed(
                    title="**MADLIBS** has timed out!",
                    descr=None,
                )
                await ctx.send(embed=embed)
                return

            # end game if timeout
            if term is not None:
                # update ALL (if linked) or just first instance with term
                if key.startswith('#'):
                    story = story.replace('{' + key + '}', term.content[1:])
                else:
                    story = story.replace('{' + key + '}', term.content[1:], 1)
                # add author of term to list
                list_of_authors.append(term.author.name)

        # tell the story (in embed)
        list_of_authors = list(set(list_of_authors))
        list_of_authors = crimsogames.winner_list(list_of_authors)
        embed = c.crimbed(
            title="{}'s madlib!".format(list_of_authors),
            descr=story,
        )
        await ctx.send(embed=embed)


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
        embed = c.crimbed(
            title="**OH MIGHTY CRIMSOBALL...**",
            descr="\n".join([
                "{} asks:".format(ctx.message.author),
                question,
                "**crimsoBOT says**: {}".format(random.choice(answer_list))
            ]),
            thumb_name="8ball",
        )
        await ctx.send(embed=embed)


    @commands.command(aliases=['guess', 'guessemoji'], brief='Guess the correct emoji from 2 to 20 choices!')
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
        if ctx.guild.id == 552650672965943296:
            winning_amount = winning_amount * server_bonus

        # the candidates
        choices = [
            '🛐', '😍', '😋', '🐍', '💩', '🌈', '🌖', '🍆', '🐧', '🥚',
            '🍌', '👺', '🧀', '😔', '🦐', '🦀', '🔥', '🍞', '🐸', '🍄'
        ]
        choices = random.sample(choices, n)
        winning_emoji = random.choice(choices)

        # initial message
        # this will be amended as the game progresses
        description = "\n".join([
            "I'm thinking of an emoji. Can you guess it?",
            "*(Multiple guesses or playing when you can't afford it will disqualify you!)*",
            "The choices are..."
        ])

        embed = c.crimbed(
            title="Let's play **GUESSMOJI!**",
            descr=description,
            footer="Choices: {:1d} · Cost: \u20A2{:.2f} · Payout: \u20A2{:.2f}".format(n, cost, winning_amount),
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
        embed.description = description + "\nYou have **eight** seconds. Go!"
        await msg.edit(embed=embed)
        await asyncio.sleep(5)

        embed.description = description + "\n**Three seconds left!**"
        await msg.edit(embed=embed)
        await asyncio.sleep(3)

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
            embed.description = "...{} guessed it for \u20A2{:.2f}!\nThe answer was {}".format(
                winners_text, winning_amount, winning_emoji
            )
        else:
            embed.description = "'...No one guessed it! The answer was {}".format(winning_emoji)

        if whammy:
            embed.description = "**WHAMMY!** Everyone loses -\u20A2{:.2f} plus the cost of the game!".format(-winning_amount)

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
    async def emojistory(self, ctx: commands.Context) -> None:
        """
        A string of emojis will appear.
        Enter a short story (<300 characters) that corresponds to the emojis, and then vote on the best story!
        The story must begin with $ to be counted.
        The winner gets a chunk of crimsoCOIN proportional the the number of votes cast for their story.

        This game requires the Manage Messages permission.
        """

        emojis = crimsogames.emojistring()

        # first embed: introduction
        timer = 63  # seconds
        embed = c.crimbed(
            title="Let's play **EMOJI STORY!**",
            descr="\n".join([
                "Invent a short story to go with the following set of emojis.",
                "Begin your story with a dollar sign **$**.",
                "You have {} seconds!".format(timer),
                emojis,
            ]),
            thumb_name="random",
        )
        await ctx.send(embed=embed)

        # define check for prefix, channel, and if author has already submitted
        def story_check(msg: discord.Message) -> bool:
            banned = self.bot.is_banned(msg.author)
            has_prefix = msg.content.startswith('$')
            just_right = 5 < len(msg.content) < 300
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
            title = "'**EMOJI STORY CANCELLED!**"
            descr = "No submissions!"
        elif len(stories) == 1:
            title = "**WINNER BY DEFAULT!**"
            descr = "\n\n".join([
                "Only one submission by **{}**:".format(stories[0].author),
                emojis,
                stories[0].content,
            ])
        else:
            title = "**VOTE NOW** for the best emoji story!"
            descr = "\n".join([
                "_ _",
                emojis,
                "_ _",
                "\n".join("{}. {}".format(stories.index(story)+1, story.content) for story in stories)
            ])
            voting = True

        # second embed: stories
        embed = c.crimbed(
            title=title,
            descr=descr,
            thumb_name="random")
        await ctx.send(embed=embed)

        # if not voting, end the thing
        if voting is False:
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
                await vote.delete()
                votes.append(vote.content)
                voters.append(vote.author)
                embed = c.crimbed(
                    title=None,
                    descr="**{}** voted.".format(vote.author),
                )
                user_has_voted_message = await ctx.send(embed=embed)
                await user_has_voted_message.delete(delay=8)

        # vote handler
        if len(votes) == 0:
            winner = None
            title = "**NO VOTES CAST!**"
            descr = "I'm disappointed."
        else:
            # send to vote counter to get winner
            ind_plus_1, votes_for_winner = crimsogames.tally(votes)
            winner = stories[int(ind_plus_1) - 1]
            winning_amount = votes_for_winner * 10
            # check if crimsoBOT home server
            if ctx.guild.id == 552650672965943296:
                winning_amount = winning_amount * server_bonus
            await crimsogames.win(winner.author, winning_amount)
            ess = "s" if votes_for_winner > 1 else ""

            # then the embed info
            title = "'**EMOJI STORY WINNER!**"
            descr = "\n\n".join([
                "The winner is **{}** with {} vote{} for their story:".format(winner.author, votes_for_winner, ess),
                emojis,
                winner.content,
            ])

        # final embed: results!
        embed = c.crimbed(
            title=title,
            descr=descr,
            thumb_name="random",
            footer="{} gets {} crimsoCOIN!".format(winner.author, winning_amount) if winner else None,
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
            title="\u200B\n{} has **\u20A2{:.2f}**.".format(whose, bal),
            descr=random.choice(encourage) if bal > 0 else "'=[",
            thumb_name="crimsoCOIN",
        )
        await ctx.send(embed=embed)


    @commands.command(aliases=['luck'])
    async def luckindex(self, ctx: commands.Context, whose: Optional[discord.Member] = None) -> None:
        """Check your or someone else's luck at Guessmoji!"""

        if not whose:
            whose = ctx.message.author

        luck, plays = await crimsogames.guess_luck_balance(whose)

        embed = c.crimbed(
            title="\u200B\n{} has a **{:.3f}** luck index on {} plays.".format(whose, 100*luck, plays),
            descr="*Luck tracking as of 01 July 2019.*",
            thumb_name="crimsoCOIN",
            footer="100 is expected · >100 means better luck · <100 means worse luck",
        )
        await ctx.send(embed=embed)


    @commands.command()
    @commands.cooldown(2, 60*30, commands.BucketType.user)
    async def give(self, ctx: commands.Context, recipient: discord.Member, amount: float) -> None:
        """Give a user up to 1/4 of your crimsoCOIN."""

        # firstly, round amount
        amount = round(amount, 2)

        # no negative values
        if amount <= 0:
            raise commands.BadArgument('Amount less than 0.')
        # not if exceeds balance
        elif amount > await crimsogames.check_balance(ctx.message.author) * 0.25:
            embed = c.crimbed(
                title="\u200B\n{}, you cannot give more than 1/4 of your balance!".format(ctx.message.author),
                descr="Check your `>balance`.",
                thumb_name="crimsoCOIN",
            )
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
            "Nice!",
            "How sweet! =]",
            "'*sucker*",
            "Give crimso some while you're at it.",
            "Your money... is GONE!",
            "You're the best!",
            "Oooh big spender"
        ]

        embed = c.crimbed(
            title='\u200B\n{} has given {} **\u20A2{:.2f}** crimsoCOIN.'.format(ctx.message.author, recipient, amount),
            descr=random.choice(encourage),
            thumb_name="crimsoCOIN",
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
            thumb_name="crimsoCOIN",
        )
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
        embed = c.crimbed(
            title=None,
            descr=result_string,
        )
        await ctx.send(embed=embed)



def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Games(bot))

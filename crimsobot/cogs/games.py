import asyncio
import random
import re
import time

import discord
from discord.ext import commands

import crimsobot.utils.games as crimsogames
import crimsobot.utils.tools as c
from config import ADMIN_USER_IDS

# lists for games in progress
madlibs_channels = []
guess_channels = []
emojistory_channels = []


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['madlib'], brief='Multiplayer mad libs! Play solo in DMs.')
    async def madlibs(self, ctx):
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
            def check(msg):
                banned = c.is_banned(msg.author.id)
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
    async def crimsoball(self, ctx, *question):
        # exception handling
        if len(question) == 0:
            return commands.MissingRequiredArgument(question)
        else:
            pass

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

        # parse out question into string
        question_ = ''
        for word in question:
            question_ += word + ' '

        # embed for answer
        title = '**OH MIGHTY CRIMSOBALL...**'
        quest = '{} asks:\n{}'.format(ctx.message.author, question_)
        answer = '**crimsoBOT says**: {}'.format(random.choice(answer_list))
        thumb = 'https://i.imgur.com/6dzqq78.png'  # 8-ball
        embed = c.crimbed(title, quest + '\n\n' + answer, thumb)

        await ctx.send(embed=embed)

    @commands.command(aliases=['guess', 'guessemoji'], brief='Guess the correct emoji from 2 to 20 choices!')
    @commands.cooldown(2, 10, commands.BucketType.user)
    async def guessmoji(self, ctx, n):
        """
        The bot will present 2 to 20 choices, depending on your selection.
        Choose only one; guessing more than once will disqualify you!
        Playing >guess 2 or >guess 3 is free. Larger Guessmoji games will cost you.
        Check your >balance! Get game costs and payouts by typing >guess costs.
        """

        # exception handling
        try:
            if not 1 <= int(n) <= 20:  # invalid amount of emojis
                raise ValueError

            # ok so if we got this far, n is an integer...
            n = int(n)
            if n == 1 and ctx.message.author.id not in ADMIN_USER_IDS:  # admins can play guess 1
                raise ValueError

            # check if user can afford to play!
            winning_amount, cost = crimsogames.guess_economy(n)
        except ValueError:
            if n == 'cost' or n == 'costs':
                costs = crimsogames.guesslist()
                content = '<:crimsoCOIN:588558997238579202> **GUESSMOJI costs and payouts:**```{}```'.format(costs)
                await ctx.send(content)

                return
            else:
                raise commands.errors.CommandInvokeError(ValueError)

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
        I'm thinking of emoji. Can you guess it?
        *(Multiple guesses or playing when you can't afford it will disqualify you!)*
        """
        thumb = None  # https://i.imgur.com/zJtRYNJ.jpg
        footer = 'Choices: {:1d} · Cost: \u20A2{:.2f} · Payout: \u20A2{:.2f}'.format(n, cost, winning_amount)

        embed = c.crimbed(title, description + 'The choices are...', thumb)
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
                await self.bot.say('**Someone added emojis!** Wait for me to add them, then choose. `Game crashed.`')

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
        winners = []
        losers = []

        # see who reacted to what
        cache_msg = discord.utils.get(self.bot.cached_messages, id=msg.id)
        for reaction in cache_msg.reactions:
            # remove the banned and poor
            players = await reaction.users().flatten()

            # only bother with this shit if someone besides the bot reacted
            if len(players) > 1:
                for player in players:
                    is_bot = player.id == self.bot.user.id
                    cannot_play = c.is_banned(player.id) or crimsogames.check_balance(player.id) < cost

                    if not is_bot and cannot_play:
                        await cache_msg.remove_reaction(reaction.emoji, player)
                        players.remove(player)

                # if winner, get winners; if not, get losers
                if reaction.emoji == winning_emoji:
                    winners = players
                else:
                    losers += players

        if len(losers) != 0:
            # kick out crimsoBOT
            losers = [user for user in losers if user.id != self.bot.user.id]

            # stats + debit the losers
            for user in losers:
                crimsogames.win(user.id, -cost)
                crimsogames.guess_luck(user.id, n, False)

        if len(winners) != 0:
            # kick out crimsoBOT
            winners = [user for user in winners if user.id != self.bot.user.id and user not in losers]

            # stats + debit & award crimsoCOIN to winners
            for user in winners:
                crimsogames.win(user.id, winning_amount - cost)
                crimsogames.guess_luck(user.id, n, True)

            # convert user objects to mentions
            winners = [user.mention for user in winners]

            # send to helper function for formatting...
            winners = crimsogames.winner_list(winners)

            # ...and change embed description
            embed.description = '...{} guessed it for \u20A2{:.2f}!\nThe answer was {}'.format(
                winners, winning_amount, winning_emoji
            )
        else:
            embed.description = '...No one guessed it! The answer was {}'.format(winning_emoji)

        # edit msg with result of game
        await msg.edit(embed=embed)

    @commands.command(brief='Make the best story based on the emojis!')
    async def emojistory(self, ctx):
        """
        A string of emojis will appear.
        Enter a short story (<250 characters) that corresponds to the emojis, and then vote on the best story!
        The story must begin with $ to be counted.

        This game requires the Manage Messages permission.
        """

        # check if running in channel
        chk = c.checkin('emojistory', ctx.message.guild, ctx.message.channel, emojistory_channels)
        if chk is False:
            raise commands.errors.CommandInvokeError('Channel in list')

        # first embed: introduction
        timer = 75  # seconds
        intro = """
        Invent a short story to go with the following set of emojis.
        Begin your story with a `$`
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
        def story_check(msg):
            banned = c.is_banned(msg.author.id)
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
            story = await self.bot.wait_for('message', check=story_check, timeout=1)
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
                str(stories.index(story) + 1) + '. {story.content}'.format(story=story) for story in stories)
            voting = True

        # second embed: stories
        embed = c.crimbed(title, descr, thumb)
        await ctx.send(embed=embed)

        # if not voting, end the thing
        if voting is False:
            c.checkout('emojistory', ctx.message.guild, ctx.message.channel, emojistory_channels)
            return

        # define check for prefix, channel, and if author has already submitted
        def vote_check(msg):
            try:
                banned = c.is_banned(msg.author.id)
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
            vote = await self.bot.wait_for('message', check=vote_check, timeout=1)
            if vote is not None:
                votes.append(vote.content)
                voters.append(vote.author)
                await vote.delete()

        # vote handler
        if len(votes) == 0:
            title = '**NO VOTES CAST!**'
            descr = "I'm disappointed."
        else:
            # send to vote counter to get winner
            ind_plus_1, votes = crimsogames.tally(votes)
            winner = stories[int(ind_plus_1) - 1]
            crimsogames.win(winner.author.id, 10)
            ess = 's' if votes > 1 else ''

            # then the embed info
            title = '**EMOJI STORY WINNER!**'
            descr = 'The winner is **{x.author}** with {y} vote{s} for their story:\n\n{e}\n\n{x.content}'.format(
                x=winner, y=votes, s=ess, e=emojis)
            footer = True

        # third embed: results!
        embed = c.crimbed(title, descr, thumb)
        if footer is True:
            embed.set_footer(text='{} gets 10 crimsoCOIN!'.format(winner.author))

        await ctx.send(embed=embed)
        c.checkout('emojistory', ctx.message.guild, ctx.message.channel, emojistory_channels)

    @commands.command(aliases=['bal'])
    async def balance(self, ctx, *user_mention):
        """Check your or someone else's crimsoCOIN balance."""

        # check for mention, else do self
        if len(ctx.message.mentions) == 1:
            # get mentioned user's avatar
            for user in ctx.message.mentions:
                whose = user
        else:
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

        bal = crimsogames.check_balance(whose.id)

        title = '\u200B\n{} has **\u20A2{:.2f}**.'.format(whose, bal)
        descr = random.choice(encourage) if bal > 0 else '=['
        thumb = 'https://i.imgur.com/rS2ec5d.png'
        embed = c.crimbed(title, descr, thumb)

        await ctx.send(embed=embed)

    @commands.command(aliases=['luck'])
    async def luckindex(self, ctx, *user_mention):
        """Check your or someone else's luck at Guessmoji!"""

        # check for mention, else do self
        if len(ctx.message.mentions) == 1:
            # get mentioned user's avatar
            for user in ctx.message.mentions:
                whose = user
        else:
            whose = ctx.message.author

        luck, plays = crimsogames.guess_luck_balance(whose.id)

        title = '\u200B\n{} has a **{:.3f}** luck index on {} plays.'.format(whose, 100 * luck, plays)
        descr = '*Luck tracking as of 01 July 2019.*'
        thumb = 'https://i.imgur.com/rS2ec5d.png'
        embed = c.crimbed(title, descr, thumb)
        embed.set_footer(text='100 is expected · >100 means better luck · <100 means worse luck')

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(2, 1 * 60 * 60, commands.BucketType.user)
    async def give(self, ctx, user_mention, amount):
        """Give a user up to 1/10 of your crimsoCOIN."""

        # thumbnail
        thumb = 'https://i.imgur.com/rS2ec5d.png'

        # firstly, change amount to float, rounded
        amount = round(float(amount), 2)

        # no negative values
        if amount <= 0:
            raise commands.CommandInvokeError('Amount less than 0.')
        # not if exceeds balance
        elif amount > crimsogames.check_balance(ctx.message.author.id) * 0.25:
            title = '\u200B\n{}, you cannot give more than 1/4 of your balance!'.format(ctx.message.author)
            descr = 'Check your `>balance`.'
            embed = c.crimbed(title, descr, thumb)
            await ctx.send(embed=embed)
            return
        else:
            pass

        # get user that is mentioned
        if len(ctx.message.mentions) == 1:
            # get mentioned user's avatar
            for user in ctx.message.mentions:
                recipient = user

        if c.is_banned(recipient.id):
            return

        # transaction
        crimsogames.win(ctx.message.author.id, -amount)  # credit
        crimsogames.win(recipient.id, amount)  # debit

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
    async def cgive(self, ctx, user_mention, amount):
        """Manual adjustment of crimsoCOIN values."""

        if ctx.message.author.id not in ADMIN_USER_IDS:
            return

        # change to float
        amount = float(amount)

        # get user that is mentioned
        if len(ctx.message.mentions) == 1:
            # get mentioned user's avatar
            for user in ctx.message.mentions:
                recipient = user

        crimsogames.win(recipient.id, amount)  # debit
        title = "\u200B\n{} has adjusted {}'s balance by {neg}\u20A2**{:.2f}**.".format(
            ctx.message.author, recipient, abs(amount), neg='-' if amount < 0 else ''
        )
        descr = 'Life is inherently unfair.' if amount < 0 else 'Rejoice in your good fortune!'
        thumb = 'https://i.imgur.com/rS2ec5d.png'
        embed = c.crimbed(title, descr, thumb)

        await ctx.send(embed=embed)

    @commands.command(aliases=['leaders', 'lb'])
    async def leaderboard(self, ctx, *args):
        """crimsoCOIN leaderboard! >lb [coin*/luck/plays] [page#]"""

        # input parser
        args = ' '.join(args)

        try:
            page = int(re.search(r'\d+', args).group())
        except Exception:
            page = 1
        if 'luck' in args:
            stat = 'luck'
        elif 'plays' in args:
            stat = 'plays'
        else:
            stat = 'coin'

        page = int(page)
        # get places from page number
        place_shift = 10 * (page - 1)
        # sorted list of CrimsoBOTUser objects
        users = crimsogames.leaders(1 + place_shift, 10 + place_shift, trait=stat)

        # add attributes in place: discord user object, place
        title = '<:crimsoCOIN_symbol:588492640559824896> crimsoCOIN leaderboard: **{}**'.format(stat.upper())
        thumb = 'https://i.imgur.com/rS2ec5d.png'
        embed = c.crimbed(title, None, thumb)
        if not users:
            embed.add_field(name="You've gone too far!",
                            value="There aren't that many players yet!",
                            inline=False)
            extra = ' does not exist.'
        else:
            for user in users:
                if stat == 'coin':
                    valstring = '\u20A2{u.coin:.2f}'.format(u=user)
                    extra = ''
                elif stat == 'plays':
                    valstring = '{u.guess_plays:.0f}'.format(u=user)
                    extra = ''
                elif stat == 'luck':
                    luck = 100 * user.guess_luck
                    valstring = '{lk:.3f} ({u.guess_plays:.0f} plays)'.format(lk=luck, u=user)
                    extra = ' · Minimum 50 plays (will increase with time)'

                user.obj = await self.bot.fetch_user(user.ID)
                user.place = users.index(user) + 1 + place_shift
                embed.add_field(name='{u.place}. **{u.obj.name}#{u.obj.discriminator}**'.format(u=user),
                                value=valstring,
                                inline=False)

        embed.set_footer(text='Page {}{}'.format(page, extra))
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def daily(self, ctx, lucky_number=0):
        """Get a daily award! Pick a number 1-100 for a chance to win bigger!"""

        # exception handling
        try:
            if not 0 <= int(lucky_number) <= 100:
                raise ValueError

            # ok so if we got this far, we can safely convert this to int
            lucky_number = int(lucky_number)
        except ValueError:
            raise commands.errors.CommandInvokeError(ValueError)

        # pass to helper and spit out result in an embed
        result_string = crimsogames.daily(ctx.message.author.id, lucky_number)
        embed = c.crimbed(None, result_string, None)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Games(bot))

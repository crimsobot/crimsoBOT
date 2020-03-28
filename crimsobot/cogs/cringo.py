import asyncio
import time
from typing import List, Optional

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import cringo, games as crimsogames, tools as c
from crimsobot.utils.cringo_leaderboard import CringoLeaderboard

# crimsoCOIN multiplier for games played in crimsoBOT server
# simple logical checks for ctx.guild.id in in each game below
server_bonus = 1.15


class Cringo(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message) -> None:
    #     """Dedicated message listener for Cringo! DMs."""
    #     if self.is_banned(message.author):
    #         return

    #     is_dm = isinstance(message.channel, discord.DMChannel)
    #     if is_dm and message.content.startswith(('.')):
    #         # do a thing

    @commands.group(aliases=['suffer'], invoke_without_command=True, brief='A quirky take on bingo.')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def cringo(self, ctx: commands.Context) -> None:
        """A peculiar blend of slots and bingo that is totally not a ripoff of a popular 1990s PC game.
        Points are awarded for matches [10], lines [100], and full card [1000].
        The earlier you get a match, line, or full card, the higher the multiplier!
        Everyone is awarded a handsome amount of crimsoCOIN for playing.
        The more players in a game, the more crimsoCOIN everyone wins!
        Play regular >cringo, >cringo mega, or >cringo mini!
        """

        # Fallback to regular four-line Cringo! if no command is provided, retains prior functionality
        await self.cringo_main(ctx, 4)

    @cringo.command(name='mega')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def mega(self, ctx: commands.Context) -> None:
        await self.cringo_main(ctx, 6)

    @cringo.command(name='mini')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def mini(self, ctx: commands.Context) -> None:
        await self.cringo_main(ctx, 2)

    async def cringo_main(self, ctx: commands.Context, card_size: int = 4) -> None:
        # depending on game size: name, thumbnail, color, cost, timer...
        name = {2: 'mini', 4: '', 6: 'MEGA'}
        thumb = {2: 'small', 4: 'jester', 6: 'scared'}
        color = {2: 'yellow', 4: 'green', 6: 'orange'}
        minimum_balance = {2: 3000, 4: 0, 6: 1000}  # NOT debited.
        timer = {2: 12, 4: 20, 6: 25}
        turns = {2: 7, 4: 9, 6: 9}

        # generate game intro embed
        join_timer = 30
        emoji = '<:crimsoCOIN:588558997238579202>'
        embed = c.crimbed(
            title="Let's play **{}CRINGO!**".format(name[card_size]),
            descr='\n'.join([
                'Click {} to join this game. You have {} seconds!'.format(emoji, join_timer),
                'Your card and instructions will be DMed to you.',
                'Gameplay happens in DM, and the scoreboard will show up here.',
            ]),
            thumb_name=thumb[card_size],
            color_name=color[card_size],
            footer='You must have a crimsoCOIN balance of {} to play!'.format(minimum_balance[card_size]),
        )
        join_message = await ctx.send(embed=embed)
        await join_message.add_reaction(emoji)

        def join_cringo(reaction: discord.reaction, user: discord.user) -> bool:
            right_game = reaction.message.id == join_message.id
            banned = self.bot.is_banned(user)
            is_bot = user.bot
            correct_reaction = str(reaction.emoji) == emoji
            already_joined = user in users_already_joined
            return right_game and not banned and not is_bot and correct_reaction and not already_joined

        # initialize join-message listener
        users_already_joined = []  # type: List[cringo.CringoPlayer]
        users_bounced = []  # type: List[cringo.DiscordUser]
        end = time.time() + join_timer
        while time.time() < end and len(users_already_joined) < 20:
            try:
                join_reaction, user_who_reacted = await self.bot.wait_for(
                    'reaction_add', check=join_cringo, timeout=join_timer
                )
            except asyncio.TimeoutError:
                continue

            if join_reaction is not None:
                embed = await cringo.process_player_joining(
                    users_already_joined,
                    users_bounced,
                    user_who_reacted,
                    minimum_balance[card_size])
                await ctx.send(embed=embed)

        # sometimes users who click aren't added; catch them here
        fetched_msg = await ctx.fetch_message(join_message.id)
        for reaction in fetched_msg.reactions:
            if str(reaction.emoji) == emoji:
                users_trying_to_join = await reaction.users().flatten()

        try:
            for user in users_trying_to_join:
                if not user.bot and user not in users_already_joined and user not in users_bounced:
                    embed = await cringo.process_player_joining(
                        users_already_joined,
                        users_bounced,
                        user,
                        minimum_balance[card_size]
                    )
                    await ctx.send(embed=embed)
        except UnboundLocalError:
            pass

        # if no one joins, end game
        if len(users_already_joined) == 0:
            embed = c.crimbed(
                title=None,
                descr='No one joined {}CRINGO! Game cancelled.'.format(name[card_size])
            )
            await ctx.send(embed=embed)
            return

        # initialize player objects
        list_of_players = []
        for player in users_already_joined:
            player_object = cringo.CringoPlayer()
            player_object.user = player
            player_object.card = await cringo.cringo_card(await cringo.cringo_emoji(card_size, card_size))
            list_of_players.append(player_object)

        # send everyone their card
        for player in list_of_players:
            try:
                await player.user.send(await cringo.deliver_card(player.card))
            except discord.errors.Forbidden:
                embed = await cringo.player_remove(list_of_players, player)
                await ctx.send(embed)

        # initial game variables
        turn_timer = timer[card_size]

        turn = 1
        total_turns = turns[card_size]
        emojis_already_used: List[str] = []

        # define check
        def player_response(msg: discord.Message) -> bool:
            begins_with_period = msg.content.startswith('.')
            is_a_player = msg.author in users_already_joined
            is_dm = isinstance(msg.channel, discord.DMChannel)
            return begins_with_period and is_a_player and is_dm

        while turn <= total_turns and len(list_of_players) > 0:
            # display initial leaderboard
            score_string, _ = await cringo.cringo_scoreboard(list_of_players)

            embed = c.crimbed(
                title='**{}CRINGO!** scoreboard'.format(name[card_size]),
                descr=score_string,
                footer='Round {}/{} coming up!'.format(turn, total_turns),
                color_name=color[card_size],
            )
            await ctx.send(embed=embed)
            await asyncio.sleep(7)

            # choose emojis, send to channel
            emojis_this_turn = await cringo.cringo_emoji(1, card_size, emojis_already_used)
            emojis_already_used.extend(emojis_this_turn[0])
            multiplier = total_turns + 1 - turn

            # send out the emojis for this turn
            embed = c.crimbed(
                title='**{}CRINGO!** Round {}/{}'.format(name[card_size], turn, total_turns),
                descr=' '.join(emojis_this_turn[0]),
                footer='{}x multiplier · {} seconds!'.format(multiplier, turn_timer),
                color_name=color[card_size],
            )
            for player in list_of_players:
                try:
                    await player.user.send(embed=embed)
                except discord.errors.Forbidden:
                    embed = await cringo.player_remove(list_of_players, player)
                    await ctx.send(embed=embed)

            # set up "listener" for players scoring their cards
            turn_end = time.time() + turn_timer
            while time.time() < turn_end:
                try:
                    response = await self.bot.wait_for('message', check=player_response, timeout=turn_timer)
                except asyncio.TimeoutError:
                    continue

                if response is not None:
                    await cringo.process_player_response(ctx, response,
                                                         list_of_players, emojis_already_used,
                                                         multiplier)

            # end of turn, time to score matches
            for player in list_of_players:
                await cringo.cringo_score(player, turn, multiplier)

            turn += 1
            if turn > total_turns:
                embed = c.crimbed(
                    title=None,
                    descr='Game over! Check the final score in <#{}>!'.format(ctx.channel.id),
                    color_name=color[card_size],
                )
            else:
                embed = c.crimbed(
                    title=None,
                    descr="Time's up! Round {} incoming.\nCheck the score in <#{}>!".format(turn, ctx.channel.id),
                    color_name=color[card_size],
                )

            # remove players with excessive mismatches
            for player in list_of_players:
                if player.mismatch_count < 8:
                    try:
                        await player.user.send(embed=embed)
                    except discord.errors.Forbidden:
                        await cringo.player_remove(list_of_players, player)
                else:
                    embed = await cringo.player_remove(list_of_players, player)
                    await ctx.send(embed=embed)

        # final score + awards time!
        # nerf calculated such that division by zero never attained within player limit
        x = len(list_of_players)
        nerf = 0.05*x**2 - 2.05*x + 52  # (points / nerf = coin)

        # check if crimsoBOT home server
        if ctx.guild and ctx.guild.id == 552650672965943296:
            nerf = (2 - server_bonus) * nerf

        score_string, winner = await cringo.cringo_scoreboard(list_of_players)

        embed = c.crimbed(
            title='**{}CRINGO!** FINAL SCORE'.format(name[card_size]),
            descr=score_string,
            footer='Your points/{:.1f}=your crimsoCOIN winnings!'.format(nerf),
            thumb_name=thumb[card_size],
            color_name=color[card_size],
        )

        # for some reason, a for loop wasn't doing the trick here...
        while len(list_of_players) != 0:
            # pull a player...
            player = list_of_players[0]
            # ...trip this is they are the winner...
            win = player.user == winner
            # ...calcuilate and give out winnings
            winning_amount = player.score/nerf
            await crimsogames.win(player.user, winning_amount)
            # ...do stats but only if regular cringo...
            if card_size == 4:
                await cringo.cringo_stats(player, winning_amount, win)
            # ...and finally remove them from list
            await cringo.player_remove(list_of_players, player)

        await ctx.send(embed=embed)

    @commands.group(aliases=['clb'], invoke_without_command=True)
    async def cringo_lb(self, ctx: commands.Context) -> None:
        """CRINGO! leaderboards!"""

        # Fallback to coin leaderboard if no command is provided, retains prior functionality
        await self.clb_coin.invoke(ctx)

    @cringo_lb.command(name='coin')
    async def clb_coin(self, ctx: commands.Context, page: int = 1) -> None:
        """CRINGO! leaderboard: COIN!"""

        lb = CringoLeaderboard(page)
        await lb.get_coin_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @cringo_lb.command(name='wins')
    async def clb_wins(self, ctx: commands.Context, page: int = 1) -> None:
        """CRINGO! leaderboard: WINS!"""

        lb = CringoLeaderboard(page)
        await lb.get_wins_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @cringo_lb.command(name='plays')
    async def clb_plays(self, ctx: commands.Context, page: int = 1) -> None:
        """CRINGO! leaderboard: PLAYS!"""

        lb = CringoLeaderboard(page)
        await lb.get_plays_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @cringo_lb.command(name='score')
    async def clb_score(self, ctx: commands.Context, page: int = 1) -> None:
        """CRINGO! leaderboard: HIGH SCORE!"""

        lb = CringoLeaderboard(page)
        await lb.get_score_leaders()
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)

    @commands.command(aliases=['stats'])
    async def cringostats(self, ctx: commands.Context, whose: Optional[discord.Member] = None) -> None:
        """Check your or someone else's CRINGO! stats!
        Stats will not be counted for incomplete games.
        Wins are counted only for games with two or more players.
        Expected average score and lines/game were found via Monte Carlo simulation (n=2.16 million).
        Expected matches/game and full cards are exact values.
        """

        if not whose:
            whose = ctx.message.author

        embed = await cringo.cringo_stat_embed(whose)
        await ctx.send(embed=embed)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Cringo(bot))

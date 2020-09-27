import asyncio
import random
from typing import List, Optional

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.context import CrimsoContext
from crimsobot.data.games import CRINGO_RULES
from crimsobot.handlers.games import CringoJoinHandler, CringoMessageHandler
from crimsobot.utils import cringo, games as crimsogames, tools as c
from crimsobot.utils.cringo import CringoPlayer
from crimsobot.utils.cringo_leaderboard import CringoLeaderboard

# crimsoCOIN multiplier for games played in crimsoBOT server
# simple logical checks for ctx.guild.id in each game below
SERVER_BONUS = 1.15


class Cringo(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.group(aliases=['suffer'], invoke_without_command=True, brief='A quirky take on bingo.')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def cringo(self, ctx: commands.Context) -> None:
        """A peculiar blend of slots and bingo that is totally not a ripoff of a popular 1990s PC game.
        Points are awarded for matches [10], lines [100], and full card [1000].
        The earlier you get a match, line, or full card, the higher the multiplier!
        Everyone is awarded a handsome amount of crimsoCOIN for playing.
        The more players in a game, the more crimsoCOIN everyone wins - assuming you don't get unlucky...
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

    async def cringo_main(self, ctx: CrimsoContext, card_size: int = 4) -> None:
        # generate game intro embed
        name_prefix = CRINGO_RULES['name'][card_size] or 'None'
        game_is_cursed = not CRINGO_RULES['name'][card_size] and random.random() > 0.98
        embed = c.crimbed(
            title=f"Let's play **{name_prefix}CRINGO!**",
            descr='\n'.join([
                'Click {} to join this game. You have {} seconds!'
                .format(CRINGO_RULES['emoji'], CRINGO_RULES['join_timer']),
                'Your card and instructions will be DMed to you.',
                'Gameplay happens in DM, and the scoreboard will show up here.',
            ]),
            thumb_name=CRINGO_RULES['thumb'][card_size],
            color_name=CRINGO_RULES['color'][card_size],
            footer='You must have a crimsoCOIN balance of {} to play!'.format(
                CRINGO_RULES['minimum_balance'][card_size]
            ),
        )

        join_message = await ctx.send(embed=embed)
        await join_message.add_reaction(CRINGO_RULES['emoji'])

        # initialize join-message listener
        join_handler = CringoJoinHandler(ctx, timeout=CRINGO_RULES['join_timer'])
        join_handler.set_arguments(emoji=CRINGO_RULES['emoji'], join_message=join_message, card_size=card_size)
        join_results = await ctx.gather_events('on_reaction_add', handler=join_handler)

        # if no one joins, end game
        if not join_results.joined:
            embed = c.crimbed(
                title=None,
                descr=f'No one joined {name_prefix}CRINGO! Game cancelled.'
            )

            await ctx.send(embed=embed)
            return

        # initialize player objects
        list_of_players: List[CringoPlayer] = []
        for player in join_results.joined:
            player_object = cringo.CringoPlayer(
                user=player,
                card=await cringo.cringo_card(await cringo.cringo_emoji(card_size, card_size))
            )

            list_of_players.append(player_object)

        # send everyone their card
        for player in list_of_players:
            try:
                await player.user.send(await cringo.deliver_card(player.card))
            except discord.errors.Forbidden:
                embed = await cringo.player_remove(list_of_players, player)
                await ctx.send(embed)

        # initial game variables
        turn_timer = CRINGO_RULES['timer'][card_size]
        turn = 1
        total_turns = CRINGO_RULES['turns'][card_size]
        emojis_already_used: List[str] = []

        while turn <= total_turns and list_of_players:
            # display initial leaderboard
            sorted_players = sorted(list_of_players, key=lambda item: item.score, reverse=True)
            score_string = await cringo.cringo_scoreboard(sorted_players)  # type: str

            embed = c.crimbed(
                title=f'**{name_prefix}CRINGO!** scoreboard',
                descr=score_string,
                footer=f'Round {turn}/{total_turns} coming up!',
                color_name=CRINGO_RULES['color'][card_size],
            )

            await ctx.send(embed=embed)
            await asyncio.sleep(7)

            # choose emojis, send to channel
            emojis_this_turn = await cringo.cringo_emoji(1, card_size, emojis_already_used)
            emojis_already_used.extend(emojis_this_turn[0])
            multiplier = total_turns + 1 - turn

            # send out the emojis for this turn
            embed = c.crimbed(
                title=f'**{name_prefix}CRINGO!** Round {turn}/{total_turns}',
                descr=' '.join(emojis_this_turn[0]),
                footer=f'{multiplier}x multiplier · {turn_timer} seconds!',
                color_name=CRINGO_RULES['color'][card_size],
            )

            for player in list_of_players:
                try:
                    await player.user.send(embed=embed)
                except discord.errors.Forbidden:
                    embed = await cringo.player_remove(list_of_players, player)
                    await ctx.send(embed=embed)

            # set up "listener" for players scoring their cards
            message_handler = CringoMessageHandler(ctx, timeout=turn_timer)
            message_handler.set_arguments(
                active_players=list_of_players,
                already_used=emojis_already_used,
                multiplier=multiplier
            )

            await ctx.gather_events('on_message', handler=message_handler)

            # end of turn, time to score matches
            for player in list_of_players:
                await cringo.cringo_score(player, turn, multiplier)

            turn += 1
            if turn > total_turns:
                embed = c.crimbed(
                    title=None,
                    descr=f'Game over! Check the final score in {ctx.channel.mention}!',
                    color_name=CRINGO_RULES['color'][card_size],
                )
            else:
                embed = c.crimbed(
                    title=None,
                    descr=f"Time's up! Round {turn} incoming.\nCheck the score in {ctx.channel.mention}!",
                    color_name=CRINGO_RULES['color'][card_size],
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
            nerf = (2 - SERVER_BONUS) * nerf

        sorted_players = sorted(list_of_players, key=lambda item: item.score, reverse=True)
        score_string = await cringo.cringo_scoreboard(sorted_players, game_is_cursed, True)

        for index, player in enumerate(list_of_players):
            # calculate and give out winnings, but give nothing to the cursed
            player.winnings = 0 if game_is_cursed else round(player.score / nerf, 1)
            await crimsogames.win(player.user, player.winnings)
            # do stats but only if regular cringo...
            if card_size == 4:
                await cringo.cringo_stats(player, index == 0)  # first in sorted list == most score

        embed = c.crimbed(
            title=f'**{name_prefix}CRINGO!** FINAL SCORE',
            descr=score_string,
            thumb_name=CRINGO_RULES['thumb'][card_size],
            color_name=CRINGO_RULES['color'][card_size],
        )

        await ctx.send(embed=embed)

    @cringo.group(name='lb', aliases=['clb'], invoke_without_command=True)
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

    @commands.command(aliases=['stats', 'cstats'])
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

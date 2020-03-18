import asyncio
import random
import time
from typing import List, Optional

import discord

# from discord import Embed

from discord.ext import commands

from config import ADMIN_USER_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.utils import cringo, games as crimsogames, tools as c


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


    @commands.command(aliases=['suffer'], brief='A quirky take on bingo.')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def cringo(self, ctx: commands.Context) -> None:
        """
        A peculiar blend of slots and bingo that is totally not a ripoff of a popular 1990s PC game.
        Points are awarded for matches [10], lines [100], and full card [1000].
        The earlier you get a match, line, or full card, the higher the multiplier!
        Everyone is awarded a handsome amount of crimsoCOIN for playing.
        The more players in a game, the more crimsoCOIN everyone wins!
        """

        # generate game intro embed
        join_timer = 45
        emoji = "<:crimsoCOIN:588558997238579202>"
        embed = c.crimbed(
            title="Let's play **CRINGO!**",
            descr="\n".join([
                "Click {} to join this game. You have {} seconds!".format(emoji, join_timer),
                "Your CRINGO! card and instructions will be DMed to you.",
                "If you didn't get instructions, unreact and re-react!",
                "Gameplay happens in DM, and the scoreboard will show up here.",
            ]),
            thumb_name="jester",
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
        users_already_joined = []
        end = time.time() + join_timer
        while time.time() < end and len(users_already_joined) < 20:
            try:
                join_reaction, user_who_reacted = await self.bot.wait_for('reaction_add', check=join_cringo, timeout=join_timer+1)
            except asyncio.TimeoutError:
                continue

            if join_reaction is not None:
                embed = await cringo.process_player_joining(users_already_joined, user_who_reacted)
                await ctx.send(embed=embed)
        
        # sometimes users who click aren't added; catch them here
        cache_msg = discord.utils.get(self.bot.cached_messages, id=join_message.id)
        for reaction in cache_msg.reactions:
            if str(reaction.emoji) == emoji:
                users_trying_to_join = await reaction.users().flatten()
        
        try:
            for user in users_trying_to_join:
                if user.id is not self.bot.user.id and user not in users_already_joined:
                    await cringo.process_player_joining(users_already_joined, user)
        except UnboundLocalError:
            pass

        # if no one joins, end game
        if len(users_already_joined) == 0:
            embed = c.crimbed(
                title=None,
                descr="No one joined! Game cancelled."
            )
            await ctx.send(embed=embed)
            return

        # initialize player objects
        list_of_players = []
        for player in users_already_joined:
            player_object = cringo.Cringo()
            player_object.player = player
            player_object.card = await cringo.cringo_card(await cringo.cringo_emoji(4))
            list_of_players.append(player_object)
        
        # send everyone their card
        for player in list_of_players:
            try:
                await player.player.send(await cringo.deliver_card(player.card))
            except discord.errors.Forbidden:
                embed = await cringo.player_remove(list_of_players, player)
                await ctx.send(embed)

        # initial game variables
        turn_timer = 25
        turn = 1
        total_turns = 9
        emojis_already_used: List[str] = []

        # define check
        def player_response(msg: discord.Message) -> bool:
            begins_with_period = msg.content.startswith('.')
            is_a_player = msg.author in users_already_joined
            is_dm = isinstance(msg.channel, discord.DMChannel)
            return begins_with_period and is_a_player and is_dm

        while turn <= total_turns and len(list_of_players) > 0:
            # display initial leaderboard
            embed = c.crimbed(
                title="**CRINGO!** scoreboard",
                descr=await cringo.cringo_scoreboard(list_of_players),
                footer="Round {}/{} coming up!".format(turn, total_turns)
            )
            await ctx.send(embed=embed)
            await asyncio.sleep(7)

            # choose emojis, send to channel
            emojis_this_turn = await cringo.cringo_emoji(1, emojis_already_used)
            emojis_already_used.extend(emojis_this_turn[0])
            multiplier = total_turns + 1 - turn

            # send out the emojis for this turn
            embed = c.crimbed(
                title="**CRINGO!** Round {}/{}".format(turn, total_turns),
                descr=' '.join(emojis_this_turn[0]),
                footer="'{}x multiplier · {} seconds!".format(multiplier, turn_timer)
            )
            for player in list_of_players:
                try:
                    await player.player.send(embed=embed)
                except discord.errors.Forbidden:
                    embed = await cringo.player_remove(list_of_players, player)
                    await ctx.send(embed=embed)

            # set up "listener" for players scoring their cards
            turn_end = time.time() + turn_timer
            while time.time() < turn_end:
                try:
                    response = await self.bot.wait_for('message', check=player_response, timeout=turn_timer+1)
                except asyncio.TimeoutError:
                    continue

                if response is not None:
                    await cringo.process_player_response(ctx, response, list_of_players, emojis_already_used, multiplier)

            # end of turn, time to score matches
            for player in list_of_players:
                await cringo.cringo_score(player, turn, multiplier)

            turn += 1
            if turn > total_turns:
                embed = c.crimbed(
                    title=None,
                    descr="Game over! Check the final score in <#{}>!".format(ctx.message.channel.id),
                )
            else:
                embed = c.crimbed(
                    title=None,
                    descr="Time's up! Round {} incoming.\nCheck the score in <#{}>!".format(turn, ctx.message.channel.id),
                )
            
            # remove players with excessive mismatches
            for player in list_of_players:
                if player.mismatch_count < 8:
                    try:
                        await player.player.send(embed=embed)
                    except discord.errors.Forbidden:
                        await cringo.player_remove(ctx, list_of_players, player)
                else:
                    await cringo.player_remove(ctx, list_of_players, player)

        # final score + awards time!
        # nerf calculated such that division by zero never attained within player limit
        x = len(list_of_players)
        nerf = 0.05*x**2 - 2.05*x + 52  # (points / nerf = coin)
        if ctx.guild.id == 552650672965943296:
            nerf = nerf * (2-server_bonus)
        for player in list_of_players:
            winning_amount = player.score/nerf
            await crimsogames.win(player.player, winning_amount)
            cringo.player_remove(list_of_players, player)

        embed = c.crimbed(
            title="**CRINGO!** FINAL SCORE",
            descr=await cringo.cringo_scoreboard(list_of_players),
            footer="Your points/{:.1f}=your crimsoCOIN winnings!".format(nerf),
            thumb_name="jester"
        )

        await ctx.send(embed=embed)



def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Cringo(bot))
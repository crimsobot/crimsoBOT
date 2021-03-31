import asyncio
import collections
import random
from typing import List, Optional, Set

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.data.games import CRINGO_RULES
from crimsobot.handlers.games import CringoJoinHandler, CringoMessageHandler
from crimsobot.utils import cringo, games as crimsogames, tools as c
from crimsobot.utils.cringo import CringoPlayer
from crimsobot.utils.cringo_leaderboard import CringoLeaderboard

# crimsoCOIN multiplier for games played in crimsoBOT server
# simple logical checks for ctx.guild.id in each game below
SERVER_BONUS = 1.15

CringoScoreboard = collections.namedtuple('CringoScoreboard', 'string winner')


class CringoGame():
    all_players: Set[int] = set()

    def __init__(self, ctx: commands.Context, *, card_size: int = 4) -> None:
        self.cursed = False
        self.name_prefix = CRINGO_RULES['name'][card_size] or ''
        if card_size == 4 and random.random() > 0.98:
            self.cursed = True
            self.name_prefix = 'None'

        # these are used during the joining phase
        self.joined: List[discord.User] = []
        self.bounced: List[discord.User] = []
        # these are used throghout the game
        self.context = ctx
        self.card_size = card_size
        self.players: List[CringoPlayer] = []
        self.turn_timer = CRINGO_RULES['timer'][card_size]
        self.turn = 1
        self.total_turns = CRINGO_RULES['turns'][card_size]
        self.minimum_balance = CRINGO_RULES['minimum_balance'][self.card_size]
        self.used_emoji: List[str] = []
        self.multiplier: int

    def generate_intro_embed(self) -> discord.Embed:
        embed = c.crimbed(
            title=f"Let's play **{self.name_prefix}CRINGO!**",
            descr='\n'.join([
                'Click {} to join this game. You have {} seconds!'
                .format(CRINGO_RULES['emoji'], CRINGO_RULES['join_timer']),
                'Your card and instructions will be DMed to you.',
                'Gameplay happens in DM, and the scoreboard will show up here.',
            ]),
            thumb_name=CRINGO_RULES['thumb'][self.card_size],
            color_name=CRINGO_RULES['color'][self.card_size],
            footer='You must have a crimsoCOIN balance of \u20A2{:.2f} to play!'.format(
                CRINGO_RULES['minimum_balance'][self.card_size]
            ),
        )

        return embed

    def generate_scoreboard_embed(self, scoreboard: CringoScoreboard) -> discord.Embed:
        embed = c.crimbed(
            title=f'**{self.name_prefix}CRINGO!** scoreboard',
            descr=scoreboard.string,
            footer=f'Round {self.turn}/{self.total_turns} coming up!',
            color_name=CRINGO_RULES['color'][self.card_size],
        )

        return embed

    def generate_game_over_embed(self, scoreboard: CringoScoreboard) -> discord.Embed:
        embed = c.crimbed(
            title=f'**{self.name_prefix}CRINGO!** FINAL SCORE',
            descr=scoreboard.string,
            thumb_name=CRINGO_RULES['thumb'][self.card_size],
            color_name=CRINGO_RULES['color'][self.card_size],
        )

        return embed

    def generate_end_of_turn_embed(self, ctx: discord.ext.commands.Context) -> discord.Embed:
        # if gameplay is in a direct message, some elements need to be handled differently
        if ctx.message.channel.type == discord.ChannelType.private:
            check_score_string = ''
        else:
            check_score_string = f'\nCheck the score in {self.context.channel.mention}!'

        if self.turn > self.total_turns:  # end of game
            embed = c.crimbed(
                title=None,
                descr=f'Game over!{check_score_string}',
                color_name=CRINGO_RULES['color'][self.card_size],
            )
        else:
            embed = c.crimbed(
                title=None,
                descr=f"Time's up! Round {self.turn} incoming.{check_score_string}",
                color_name=CRINGO_RULES['color'][self.card_size],
            )

        return embed

    def generate_join_test_message_embed(self) -> discord.Embed:
        embed = c.crimbed(
            title='Welcome to **CRINGO!**',
            descr='\n'.join([
                'Match the emojis called to the emojis on your card.',
                'If you see a match, type the column and row of the match!',
                'Type `.<letter><number>` or `. <letter><number>`.',
                'You can put in multiple matches separated by a space!',
                'For example: `.a1 b2 c4` or `. b4 c3`. Only use one period!',
                'Missed a match on a previous turn? No problem! Put it in anyway.',
                "You'll still get your points (but with a lower multiplier).",
                'Need to leave the game? Type `.leave` during a round.',
            ]),
            thumb_name='jester'
        )

        return embed

    def generate_join_no_dms_embed(self, who: discord.Member) -> discord.Embed:
        embed = c.crimbed(
            title=f'Uh oh, **{who} CANNOT** join the game!',
            descr='You have to be able to receive DMs from crimsoBOT to play!',
            color_name='orange',
            thumb_name='weary'
        )

        return embed

    def generate_join_low_balance_embed(self, who: discord.Member) -> discord.Embed:
        embed = c.crimbed(
            title=f'Uh oh, **{who} CANNOT** join the game!',
            descr='\n'.join([
                '· You must have a balance of \u20A2{:.2f} to play this game!'
                .format(CRINGO_RULES['minimum_balance'][self.card_size]),
                "· Don't fret; regular CRINGO! can be played by anyone!",
            ]),
            color_name='orange',
            thumb_name='moneymouth'
        )

        return embed

    def generate_join_already_playing_embed(self, who: discord.Member) -> discord.Embed:
        embed = c.crimbed(
            title=f'Uh oh, **{who} CANNOT** join the game!',
            descr="You're already playing another game of CRINGO! aren't you?",
            color_name='orange',
            thumb_name='think'
        )

        return embed

    def generate_join_success_embed(self, who: discord.Member) -> discord.Embed:
        embed = c.crimbed(
            title='',
            descr=f'**{who}** has joined the game!',
            color_name='green',
            thumb_name=''
        )

        return embed

    def generate_mismatch_embed(self) -> discord.Embed:
        embed = c.crimbed(
            title=None,
            descr='Mismatch(es) detected. You lose points for that!',
            color_name='orange',
        )

        return embed

    def remove_from_game(self, user: discord.User) -> discord.Embed:
        player = [player for player in self.players if player.user == user]
        if player:
            self.players.remove(player[0])

        CringoGame.all_players.discard(user.id)
        embed = c.crimbed(
            title=None,
            descr=f'{user} has left the game.',
            color_name='yellow',
        )

        return embed

    def get_scoreboard(self, *, game_finished: bool = False) -> CringoScoreboard:
        scoreboard_rows = []
        sorted_players = sorted(self.players, key=lambda item: item.score, reverse=True)
        for player in sorted_players:
            coin_display = 'zero' if self.cursed else round(player.winnings, 2)
            if game_finished:
                row = f'{player.user} · **{player.score}** points · **\u20A2{coin_display}**'
            else:
                row = f'{player.user} · **{player.score}** points'

            scoreboard_rows.append(row)

        if sorted_players:
            winner: Optional[CringoPlayer] = sorted_players[0]
        else:
            winner = None
            scoreboard_rows = [
                f'It looks like everybody has left this {self.name_prefix}CRINGO! game!',
                'Finish the game next time you cowards.'
            ]

        return CringoScoreboard('\n'.join(scoreboard_rows), winner)

    def prettify_card(self, card: List[List[str]]) -> str:
        # we add the blank emoji to the first line to accommodate compact mode w/o resizing emojis
        pretty_string = '\n'.join('\u200A'.join(sublist) for sublist in card)
        return f'<:blank:589560784485613570>\n{pretty_string}'

    async def send_cards(self) -> None:
        for player in self.players.copy():
            try:
                pretty_card = self.prettify_card(player.card)
                await player.user.send(pretty_card)
            except discord.errors.Forbidden:
                self.players.remove(player)
                CringoGame.all_players.discard(player.user.id)
                embed = c.crimbed(
                    title=None,
                    descr=f'{player.user} has left the game.',
                    color_name='yellow',
                )

                await self.context.send(embed)

    async def send_emojis(self, emojis: List[List[str]]) -> None:
        embed = c.crimbed(
            title=f'**{self.name_prefix}CRINGO!** Round {self.turn}/{self.total_turns}',
            descr=' '.join(emojis[0]),
            footer=f'{self.multiplier}x multiplier · {self.turn_timer} seconds!',
            color_name=CRINGO_RULES['color'][self.card_size],
        )

        for player in self.players.copy():
            try:
                await player.user.send(embed=embed)
            except discord.errors.Forbidden:
                self.players.remove(player)
                CringoGame.all_players.discard(player.user.id)

                await self.context.send(embed)

    # this function is called by the join handler
    async def process_player_joining(self, user: discord.User) -> discord.Embed:
        current_balance = await crimsogames.check_balance(user)  # cost is NOT debited.
        not_enough_coin = current_balance < (self.minimum_balance if self.minimum_balance != 0 else float('-inf'))

        # deny the poor of any opportunities
        if not_enough_coin:
            return self.generate_join_low_balance_embed(user)

        # they're already playing!
        if user.id in CringoGame.all_players:
            self.bounced.append(user)
            return self.generate_join_already_playing_embed(user)

        # see if we can send them messages, and if so, add them to the game
        try:
            embed = self.generate_join_test_message_embed()
            await user.send(embed=embed)
            self.joined.append(user)
            CringoGame.all_players.add(user.id)
            return self.generate_join_success_embed(user)
        except discord.errors.Forbidden:
            self.bounced.append(user)
            return self.generate_join_no_dms_embed(user)

    # this function is called by the response handler
    async def process_player_response(self, response: discord.Message) -> None:
        try:  # find the player object of the response author
            player = [player for player in self.players if player.user == response.author][0]
        except IndexError:  # this player somehow isn't in the game? just ignore them
            return

        # determine if user's response is a match
        # matches missed in previous rounds are OK (they only lose the earlier round multiplier)
        positions: List[str] = response.content.replace('.', '').strip().split(' ')
        mismatch_detected = False
        for position in positions:
            if position == 'leave':  # evict them if they ask
                embed = self.remove_from_game(player.user)
                await self.context.send(embed=embed)
                return

            # if they're still in the game, then check for matches
            match = await cringo.mark_card(player, position, self.used_emoji, self.multiplier)

            if not match:
                mismatch_detected = True

        # mismatch message is sent only once
        if mismatch_detected:
            embed = self.generate_mismatch_embed()
            await response.author.send(embed=embed)

        await response.author.send(self.prettify_card(player.card))

    # this is where the majority of game logic is
    async def start(self) -> None:
        join_embed = self.generate_intro_embed()
        join_message = await self.context.send(embed=join_embed)
        await join_message.add_reaction(CRINGO_RULES['emoji'])

        # initialize listener for join messages
        join_handler = CringoJoinHandler(self.context, timeout=CRINGO_RULES['join_timer'])
        join_handler.set_arguments(emoji=CRINGO_RULES['emoji'], join_message=join_message, game=self)
        await self.context.gather_events('on_reaction_add', handler=join_handler)

        # if nobody joins, end game
        if not self.joined:
            embed = c.crimbed(
                title=None,
                descr=f'No one joined {self.name_prefix}CRINGO! Game cancelled.'
            )

            await self.context.send(embed=embed)
            return

        # prepare player list
        for player in self.joined:
            cringo_emojis = await cringo.cringo_emoji(self.card_size, self.card_size)
            new_player = cringo.CringoPlayer(
                user=player,
                card=await cringo.cringo_card(cringo_emojis)
            )

            self.players.append(new_player)
            # we don't need to manipulate CringoGame.all_players here as it's done inside of the join handler

        # send everyone their cards
        await self.send_cards()

        while self.turn <= self.total_turns and self.players:
            scoreboard = self.get_scoreboard()
            scoreboard_embed = self.generate_scoreboard_embed(scoreboard)
            await self.context.send(embed=scoreboard_embed)
            await asyncio.sleep(7)

            emojis_this_turn = await cringo.cringo_emoji(1, self.card_size, self.used_emoji)
            self.used_emoji.extend(emojis_this_turn[0])
            self.multiplier = self.total_turns + 1 - self.turn
            await self.send_emojis(emojis_this_turn)

            # set up listener for players scoring their cards
            message_handler = CringoMessageHandler(self.context, timeout=self.turn_timer)
            message_handler.set_arguments(game=self)

            await self.context.gather_events('on_message', handler=message_handler)

            # end of turn, time to score everything
            for player in self.players:
                await cringo.cringo_score(player, self.turn, self.multiplier)  # type: ignore

            self.turn += 1

            # remove players who have too many mismatches
            turn_embed = self.generate_end_of_turn_embed(self.context)
            for player in self.players.copy():
                if player.mismatch_count >= 8:
                    left_game_embed = self.remove_from_game(player.user)
                    await self.context.send(embed=left_game_embed)
                    continue

                # tell players what happens at the end of this turn
                try:
                    await player.user.send(embed=turn_embed)
                except discord.errors.Forbidden:
                    self.remove_from_game(player.user.id)

        # final score + awards time!
        # nerf calculated such that division by zero never attained within player limit
        x = len(self.players)
        nerf = 0.05*x**2 - 2.05*x + 52  # (points / nerf = coin)

        # check if crimsoBOT home server
        if self.context.guild and self.context.guild.id == 552650672965943296:
            nerf = (2 - SERVER_BONUS) * nerf

        # process all scores & winnings
        for player in self.players:
            player.winnings = 0 if self.cursed else player.score / nerf
            await crimsogames.win(player.user, player.winnings)
            CringoGame.all_players.discard(player.user.id)  # some final cleanup

        # now that we have our winnings calculated, generate a scoreboard with winnings and run through players again
        # to record stats for them
        final_scoreboard = self.get_scoreboard(game_finished=True)
        if self.card_size == 4:
            for player in self.players:
                await cringo.cringo_stats(player, player == final_scoreboard.winner)

        embed = self.generate_game_over_embed(final_scoreboard)
        await self.context.send(embed=embed)


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
        await CringoGame(ctx).start()

    @cringo.command(name='mega')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def mega(self, ctx: commands.Context) -> None:
        await CringoGame(ctx, card_size=6).start()

    @cringo.command(name='mini')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def mini(self, ctx: commands.Context) -> None:
        await CringoGame(ctx, card_size=2).start()

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

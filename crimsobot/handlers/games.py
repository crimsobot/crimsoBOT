from typing import List, TYPE_CHECKING

import discord

from crimsobot.data.games import EMOJISTORY_RULES
from crimsobot.handlers import AbstractEventGatherer, StopHandler, must_be_event
from crimsobot.utils import cringo, tools as c

# prevents a circular import
if TYPE_CHECKING:
    from crimsobot.cogs.cringo import CringoGame


@must_be_event('on_reaction_add')
class CringoJoinHandler(AbstractEventGatherer):
    def _can_join_cringo(
        self,
        reaction: discord.Reaction,
        join_message: discord.Message,
        user: cringo.DiscordUser
    ) -> bool:
        right_game = reaction.message.id == join_message.id
        correct_reaction = str(reaction.emoji) == self.emoji
        already_joined = user in self.game.joined or user in self.game.bounced
        return right_game and not self.bot.is_banned(user) and not user.bot and correct_reaction and not already_joined

    async def on_attach(self, *, emoji: str, join_message: discord.Message, game: 'CringoGame') -> None:  # type: ignore
        self.emoji = emoji
        self.game = game
        self.card_size = game.card_size
        self.join_message = join_message

    async def on_event(self, reaction: discord.Reaction, user: discord.User) -> None:  # type: ignore
        if self._can_join_cringo(reaction, self.join_message, user):
            embed = await self.game.process_player_joining(user)
            await self.context.send(embed=embed)

        if len(self.game.joined) >= 20:
            raise StopHandler


@must_be_event('on_message')
class CringoMessageHandler(AbstractEventGatherer):
    def _is_valid_player_response(self, message: discord.Message) -> bool:
        begins_with_period = message.content.startswith('.')
        is_a_player = message.author in [player.user for player in self.game.players]
        is_dm = isinstance(message.channel, discord.DMChannel)
        return begins_with_period and is_a_player and is_dm

    async def on_attach(self, *, game: 'CringoGame') -> None:  # type: ignore
        self.game = game

    async def on_event(self, message: discord.Message) -> None:  # type: ignore
        if self._is_valid_player_response(message):
            await self.game.process_player_response(message)


@must_be_event('on_message')
class EmojistorySubmissionHandler(AbstractEventGatherer):
    def _story_check(self, message: discord.Message) -> bool:
        banned = self.bot.is_banned(message.author)
        has_prefix = message.content.startswith('$')
        just_right = EMOJISTORY_RULES['minimum_length'] < len(message.content) < EMOJISTORY_RULES['maximum_length']
        in_channel = message.channel == self.context.message.channel
        is_author = message.author in self.authors
        return not banned and has_prefix and just_right and in_channel and not is_author

    async def on_attach(self) -> None:  # type: ignore
        self.stories = []  # type: List[discord.Message]
        self.authors = []  # type: List[discord.Member]

    async def on_event(self, message: discord.Message) -> None:  # type: ignore
        if self._story_check(message):
            self.stories.append(message)
            self.authors.append(message.author)
            await message.delete()

            embed = c.crimbed(
                title=None,
                descr='Story submitted!',
            )

            await self.context.send(embed=embed, delete_after=5)


@must_be_event('on_message')
class EmojistoryVotingHandler(AbstractEventGatherer):
    def _vote_check(self, message: discord.Message) -> bool:
        try:
            choice = int(message.content)
        except ValueError:
            return False

        banned = self.bot.is_banned(message.author)
        in_channel = message.channel == self.context.message.channel
        valid_choice = 0 < choice <= len(self.stories)
        has_voted = message.author in self.voters
        return not banned and valid_choice and in_channel and not has_voted

    async def on_attach(self, stories: List[discord.Message]) -> None:  # type: ignore
        self.stories = stories  # type: List[discord.Message]
        self.votes = []  # type: List[discord.Message]
        self.voters = []  # type: List[discord.Member]

    async def on_event(self, message: discord.Message) -> None:  # type: ignore
        if self._vote_check(message):
            await message.delete()
            self.votes.append(message.content)
            self.voters.append(message.author)

            embed = c.crimbed(
                title=None,
                descr=f'**{message.author.name}** voted.',
            )

            await self.context.send(embed=embed, delete_after=8)

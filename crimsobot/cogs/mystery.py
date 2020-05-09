import asyncio

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import tarot
from crimsobot.utils import tools as c
from crimsobot.utils.tarot import Deck, Suit


class Mystery(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.command(brief='Tarot readings by crimsoBOT.')
    @commands.cooldown(3, 300, commands.BucketType.user)
    async def tarot(self, ctx: commands.Context, spread: str = 'ppf') -> None:
        """Do you seek wisdom and guidance?
        Unveil the Mysteries of the past, the present, and the future with a tarot reading.
        A brief meaning of each card appears next to its name.
        Meditate deeply upon the words of wise crimsoBOT, and all shall become clear...

        >tarot ppf
        This three-card spread is read from left to right to explore your past, present, and future.

        >tarot five
        This spread delves deeper into the present, exploring your Reason for seeking guidance.
        The Future card speaks toward the outcome should you stay on your current path.
        The Potential card looks toward the outcome should you change paths.

        You may choose to have a specific question in mind before you ask for your cards.
        However, taking a reading without a question in mind
            may help coax from you the reason you seek the tarot's guidance.

        ABOUT THE DECK

        The Major Arcana:
        Beginning with The Fool and ending with The World, these 22 cards represent major archetypes.
        They indicate great cosmic forces at work. Be especially attentive to what they have to say.

        The Minor Arcana of 56 cards is divided into four suits. These are:

        • The Wands: The Wands are ruled by the element of fire.
        Their sphere of influence is energy, motivation, will, and passion:
        that which most deeply animates and ignites the soul.

        • The Pentacles: Ruled by the element of earth.
        The Pentacles deal with earthly matters--
        health, finances, the body, the domestic sphere, and one's sense of security.

        • The Cups: The Cups are ruled by the element of water.
        They preside over matters of the heart.
        Emotion, relationships, inutition, and mystery are all found within their depths.

        • The Swords: The Swords are ruled by the element of air.
        Their main concern is the mind and the intellect.
        They cut through delusion towards clarity with sometimes unforgiving sharpness.
        """

        fp, descriptions = await tarot.reading(spread)
        await ctx.send('\n'.join(descriptions), file=discord.File(fp, 'reading.png'))

    @commands.command(aliases=['tarotcard'], brief='Inspect a tarot card for further study.')
    async def card(self, ctx: commands.Context) -> None:
        """Inspect a tarot card chosen from the menu for further study.
        See also >help tarot for more info about the Major Arcana and the four suits."""

        # the suits
        suits = [s for s in Suit]
        suit_list = []
        for idx, suit in enumerate(suits):
            suit_list.append('{}. {}'.format(idx + 1, suit))

        # prompt 1 of 2: choose suit
        embed = c.crimbed(
            title='Choose a suit:',
            descr='\n'.join(suit_list),
            thumb_name='wizard',
            footer='Type the number to choose.'
        )
        prompt_suit = await ctx.send(embed=embed)

        # define check for suit
        def suit_check(msg: discord.Message) -> bool:
            try:
                valid_choice = 0 < int(msg.content) <= len(suits)
                in_channel = msg.channel == ctx.message.channel
                is_author = msg.author == ctx.message.author

                return valid_choice and in_channel and is_author

            except ValueError:
                return False

        # wait for user to spcify suit
        try:
            msg = await self.bot.wait_for('message', check=suit_check, timeout=20)
        except asyncio.TimeoutError:
            await prompt_suit.delete()
            return

        await prompt_suit.delete()

        if msg is None:
            return

        suit_choice = int(msg.content)
        await msg.delete()

        # prompt 2 of 2: choose card in suit
        suit = suits[suit_choice - 1]
        cards = await Deck.get_cards_in_suit(suit)
        card_list = []
        for card in cards:
            card_list.append('{}. {}'.format(card.number, card.name))

        embed = c.crimbed(
            title='Choose a card:',
            descr='\n'.join(card_list),
            thumb_name='wizard',
            footer='Type the number to choose.',
        )
        prompt_card = await ctx.send(embed=embed)

        # define check for card
        def card_check(msg: discord.Message) -> bool:
            try:
                card_numbers = [c.number for c in cards]
                valid_choice = int(msg.content) in card_numbers
                in_channel = msg.channel == ctx.message.channel
                is_author = msg.author == ctx.message.author

                return valid_choice and in_channel and is_author

            except ValueError:
                return False

        # wait for user to spcify suit
        try:
            msg = await self.bot.wait_for('message', check=card_check, timeout=20)
        except asyncio.TimeoutError:
            await prompt_card.delete()
            return

        await prompt_card.delete()

        if msg is None:
            return

        card_number = int(msg.content)
        await msg.delete()

        card = await Deck.get_card(suit, card_number)
        description = '**{}**\n**Upright:** {}\n**Reversed:** {}'.format(
            card.name.upper(), card.description_upright, card.description_reversed
        )
        fp = await card.get_image_buff()
        await ctx.send(description, file=discord.File(fp, 'card.png'))


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Mystery(bot))

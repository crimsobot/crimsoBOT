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

    @commands.group(invoke_without_command=True, brief='Delve into the mysteries of tarot.')
    async def tarot(self, ctx: commands.Context) -> None:
        """Do you seek wisdom and guidance?
        Unveil the Mysteries of the past, the present, and the future with a tarot reading.
        A brief meaning of each card appears next to its name.
        Meditate deeply upon the words of wise crimsoBOT, and all shall become clear...

        You may choose to have a specific question in mind before you ask for your cards.
        However, taking a reading without a question in mind
            may help coax from you the reason you seek the tarot's guidance.
        """

        # if no subcommand provided, give a three-card reading
        await self.ppf(ctx)

    @tarot.command(name='one', brief='Get a single card.')  # something better needs to be put here, i do not know much
    @commands.cooldown(3, 300, commands.BucketType.user)
    async def one(self, ctx: commands.Context, spread: str = 'one') -> None:
        """ One card """  # this also needs to be improved

        fp, descriptions = await tarot.reading(spread)
        filename = 'reading.png'
        f = discord.File(fp, 'reading.png')

        embed = c.crimbed(
            title="{}'s reading".format(ctx.author),
            descr=None,
            attachment=filename,
            footer='Type ">tarot card" for more on a specific card.',
        )

        for card_tuple in descriptions:
            embed.add_field(name=card_tuple[0], value='**{}**\n{}'.format(card_tuple[1], card_tuple[2]))

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='ppf', brief='Past, present, and future.')
    @commands.cooldown(3, 300, commands.BucketType.user)
    async def ppf(self, ctx: commands.Context, spread: str = 'ppf') -> None:
        """This three-card spread is read from left to right to explore your past, present, and future."""

        fp, descriptions = await tarot.reading(spread)
        filename = 'reading.png'
        f = discord.File(fp, filename)

        embed = c.crimbed(
            title="{}'s reading".format(ctx.author),
            descr=None,
            attachment=filename,
            footer='Type ">tarot card" for more on a specific card.',
        )

        card_tuple = descriptions[0]
        embed.add_field(name=card_tuple[0], value='**{}**\n{}'.format(card_tuple[1], card_tuple[2]))

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='five', brief='Look deeper into your Reason and Potential.')
    @commands.cooldown(3, 300, commands.BucketType.user)
    async def five(self, ctx: commands.Context, spread: str = 'five') -> None:
        """This spread delves deeper into the present, exploring your Reason for seeking guidance.
        The Future card speaks toward the outcome should you stay on your current path.
        The Potential card looks toward the outcome should you change paths."""

        fp, descriptions = await tarot.reading(spread)
        filename = 'reading.png'
        f = discord.File(fp, filename)

        embed = c.crimbed(
            title="{}'s reading".format(ctx.author),
            descr=None,
            attachment=filename,
            footer='Type ">tarot card" for more on a specific card.',
        )

        for card_tuple in descriptions:
            embed.add_field(name=card_tuple[0], value='**{}**\n{}'.format(card_tuple[1], card_tuple[2]))

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='card', brief='Inspect an individual card.')
    async def card(self, ctx: commands.Context) -> None:
        """Inspect an individual tarot card. A longer description is given for each."""

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
            msg = await self.bot.wait_for('message', check=suit_check, timeout=45)
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

        fp = await card.get_image_buff()
        filename = 'card.png'
        f = discord.File(fp, filename)

        embed = c.crimbed(
            title='**{}**'.format(card.name.upper()),
            descr='\n'.join([
                '**Element:** {}'.format(card.element),
                '**Upright:** {}'.format(card.description_upright),
                '**Reversed:** {}'.format(card.description_reversed),
                '\n{}'.format(card.description_long),
            ]),
            attachment=filename,
        )
        await ctx.send(file=f, embed=embed)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Mystery(bot))

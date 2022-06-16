import asyncio

import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import tarot
from crimsobot.utils import tools as c
from crimsobot.utils.tarot import Card, Deck


class Mystery(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    async def prompt_for_single_card(self, ctx: commands.Context) -> Card:
        """Prompt user to choose first a suit, then a card from chosen suit."""

        # prompt 1 of 2: choose suit
        suits = await Deck.get_suits()
        suit_list = []
        for suit in suits:
            suit_list.append(f'**{suit.number}. {suit.name}**\n{suit.description}')

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
                valid_choice = 0 <= int(msg.content) < len(suits)
                in_channel = msg.channel == ctx.message.channel
                is_author = msg.author == ctx.message.author

                return valid_choice and in_channel and is_author

            except ValueError:
                return False

        # wait for user to specify suit
        try:
            msg = await self.bot.wait_for('message', check=suit_check, timeout=75)
        except asyncio.TimeoutError:
            await prompt_suit.delete()
            raise

        await prompt_suit.delete()

        suit_choice = int(msg.content)
        await msg.delete()

        # prompt 2 of 2: choose card in suit
        suit = suits[suit_choice]

        cards = await Deck.get_cards_in_suit(suit)
        card_list = []
        for card in cards:
            card_list.append(f'{card.number}. {card.name}')

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

        # wait for user to specify card
        try:
            msg = await self.bot.wait_for('message', check=card_check, timeout=30)
        except asyncio.TimeoutError:
            await prompt_card.delete()
            raise

        await prompt_card.delete()

        card_number = int(msg.content)
        await msg.delete()

        return await Deck.get_card(suit, card_number)

    @commands.group(invoke_without_command=True, brief='Delve into the mysteries of tarot.')
    @commands.cooldown(3, 300, commands.BucketType.user)
    async def tarot(self, ctx: commands.Context) -> None:
        """Do you seek wisdom and guidance?
        Unveil the Mysteries of the past, the present, and the future with a tarot reading.
        A brief meaning of each card appears next to its name.
        Meditate deeply upon the words of wise crimsoBOT, and all shall become clear...

        You may choose to have a specific question in mind before you ask for your cards.
        However, taking a reading without a question in mind
            may help coax from you the reason you seek the tarot's guidance.
        """

        # if no subcommand is provided, we give a three-card reading.
        # However, before invoking the command, we make sure that it can be run. If the command cannot be run, can_run
        # will error and the error will propogate normally. For some odd reason this doesn't catch cooldowns - even
        # though it should. Whatever. This command has a cooldown so it's fine.

        await self.ppf.can_run(ctx)
        await self.ppf(ctx)

    @tarot.command(name='one', aliases=['1'], brief='Get a single-card reading.')
    @commands.cooldown(3, 120, commands.BucketType.user)
    async def one(self, ctx: commands.Context, spread: str = 'one') -> None:
        """This single-card reading is your answer to any question you may have."""

        fp, descriptions = await tarot.reading(spread)
        filename = 'reading.png'
        f = discord.File(fp, 'reading.png')

        embed = c.crimbed(
            title=f"{ctx.author}'s reading",
            descr=None,
            attachment=filename,
            footer='Type ">tarot card" for more on a specific card.',
        )

        card_tuple = descriptions[0]
        embed.description = f'**{card_tuple[1]}**\n{card_tuple[2]}'

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='major', brief='Draw a single Major Arcana card.')
    @commands.cooldown(3, 120, commands.BucketType.user)
    async def major(self, ctx: commands.Context, spread: str = 'major') -> None:
        """A single-card reading from the Major Arcana."""

        fp, descriptions = await tarot.reading(spread)
        filename = 'reading.png'
        f = discord.File(fp, 'reading.png')

        embed = c.crimbed(
            title=f"{ctx.author}'s reading",
            descr=None,
            attachment=filename,
            footer='Type ">tarot card" for more on a specific card.',
        )

        card_tuple = descriptions[0]
        embed.description = f'**{card_tuple[1]}**\n{card_tuple[2]}'

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='ppf', aliases=['3', 'three'], brief='Past, present, and future.')
    @commands.cooldown(3, 120, commands.BucketType.user)
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

        for card_tuple in descriptions:
            embed.add_field(
                name=card_tuple[0],
                value=f'**{card_tuple[1]}**\n{card_tuple[2]}',
            )

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='major3', aliases=['majorthree'], brief='Past, present, and future from the Major Arcana.')
    @commands.cooldown(3, 120, commands.BucketType.user)
    async def major3(self, ctx: commands.Context, spread: str = 'major3') -> None:
        """This spread of Major Arcana cards is read from left to right to explore your past, present, and future."""

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
            embed.add_field(
                name=card_tuple[0],
                value=f'**{card_tuple[1]}**\n{card_tuple[2]}',
            )

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='cross', aliases=['5', 'five'], brief='Look deeper into your Reason and Potential.')
    @commands.cooldown(3, 120, commands.BucketType.user)
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
            embed.add_field(
                name=card_tuple[0],
                value=f'**{card_tuple[1]}**\n{card_tuple[2]}',
            )

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='celtic', brief='The Celtic Cross spread.')
    @commands.cooldown(3, 120, commands.BucketType.user)
    async def celtic(self, ctx: commands.Context, spread: str = 'celtic') -> None:
        """This spread presents the Cross of the current situation and the Pillar of influences."""

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
            embed.add_field(
                name=card_tuple[0],
                value=f'**{card_tuple[1]}**\n{card_tuple[2]}',
            )

        await ctx.send(file=f, embed=embed)

    @tarot.command(name='card', brief='Inspect an individual card.')
    @commands.max_concurrency(1, commands.BucketType.user)  # To avoid a 404: Unknown Message & other oddities
    async def card(self, ctx: commands.Context, *, card_name: str = '') -> None:
        """Inspect an individual tarot card. A longer description is given for each."""

        if card_name:
            card = await Deck.get_card_by_name(card_name)  # type: Card
        else:
            try:
                card = await self.prompt_for_single_card(ctx)
            except asyncio.TimeoutError:
                return

        suit = await Deck.get_suit(card.suit)

        fp = await card.get_image_file()
        filename = 'card.png'
        f = discord.File(fp, filename)

        embed = c.crimbed(
            title=f'**{card.name.upper()}** · {card.element}',
            descr='\n\n'.join([
                f'**Upright:** *{card.description_upright}*',
                card.description_long,
                f'**Reversed:** *{card.description_reversed}*',
                card.description_long_reversed,
            ]),
            attachment=filename,
            footer=suit.description,
        )
        await ctx.send(file=f, embed=embed)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Mystery(bot))

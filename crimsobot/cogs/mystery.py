import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils import tarot


class Mystery(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.command(brief='Tarot readings by crimsoBOT.')
    @commands.cooldown(3, 300, commands.BucketType.user)
    async def tarot(self, ctx: commands.Context, spread: str = 'ppf') -> None:
        """
        Do you seek wisdom and guidance?
        Unveil the Mysteries of the past, the present, and the future with a quick tarot card reading.
        Based on the classic Rider-Waite tarot deck, this three-card spread is read from left to right.
        The first card deals with the past, the second with the present, and the third with the future.
        The meaning of each card appears next to its name.
        Meditate deeply upon the words of wise crimsoBOT, and all shall become clear...

        You may choose to have a specific question in mind before you ask for your cards.
        This may help you interpret the spread before you.

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

        fp, descriptions = tarot.reading(spread)
        await ctx.send('\n'.join(descriptions), file=discord.File(fp, 'reading.png'))


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Mystery(bot))

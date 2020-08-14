import re

from discord.ext import commands

from crimsobot.utils import tools as c


with open(c.clib_path_join('text', 'emojiregex.txt')) as regex_file:
    pattern = regex_file.read()

ABSURD_PATTERN = re.compile(pattern)


class CleanMentions(commands.Converter):
    async def convert(self, ctx: commands.Context, string: str) -> str:
        """Clean up those silly mention inconsistencies across platforms."""
        for mention in ctx.message.mentions:
            string = string.replace(f'<@!{mention.id}>', f'<@{mention.id}>', 1)

        return string


class CleanedTextInput(commands.Converter):
    def __init__(self, char_limit: int = 10) -> None:
        self.char_limit = char_limit

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        """Get some proper emoji/text input."""
        # check and clean the input
        if len(argument) > self.char_limit:
            # check if input is a custom emoji we have access to
            emoji_strings = [str(e) for e in ctx.bot.emojis]
            if argument not in emoji_strings:
                return ''

        return argument.strip().strip('\n|\u200b\u200d')


class AbsurdEmojiConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        """Get some PROPER emoji input."""
        # check if input is a custom emoji we have access to
        emoji_strings = [str(e) for e in ctx.bot.emojis]
        if argument in emoji_strings:
            return argument

        match = re.match(ABSURD_PATTERN, argument)
        if match:
            return match[0]

        raise commands.BadArgument

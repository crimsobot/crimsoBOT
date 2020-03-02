import functools
import random as r
import re
import time
from typing import Any, Callable, List

import markovify
import nltk
from discord.ext.commands import Bot

from crimsobot.utils import tools as c


class POSifiedText(markovify.Text):
    def word_split(self, sentence: str) -> List[str]:
        words = re.split(self.word_split_pattern, sentence)
        words = ['::'.join(tag) for tag in nltk.pos_tag(words)]

        return words

    def word_join(self, words: List[str]) -> str:
        sentence = ' '.join(word.split('::')[0] for word in words)

        return sentence


def learner(msg: str) -> None:
    with open(c.clib_path_join('text', 'crimso.txt'), 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % msg)


def scraper(msg: str) -> None:
    with open(c.clib_path_join('text', 'scrape.txt'), 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % msg)


def scatter(msg_list: List[str]) -> str:
    """Write text file from list of strings."""
    
    one_long_string = '\n'.join(msg_list)
    one_long_string = one_long_string.upper()

    factor = 1

    model = markovify.NewlineText(one_long_string, state_size=factor)
    
    # sometimes this process will fail to make a new sentence if the corpus is too short or lacks variety.
    # so I let it try for 8 seconds to do the thing, but kill it after that.
    now = time.time()
    out = None
    while time.time() < now + 5:
        if out is None:
            out = model.make_short_sentence(r.randint(40, 400))
            if out is not None:
                break

    if out is None:
        out = "NO."

    return out


def poem(number_lines: int) -> str:
    """Write a poem."""

    with open(c.clib_path_join('text', 'all.txt'), encoding='utf8', errors='ignore') as f:
        text1 = f.read()

    with open(c.clib_path_join('text', 'randoms.txt'), encoding='utf8', errors='ignore') as f:
        text2 = f.read()

    poem_factor = 2
    crimso_model = markovify.Text(text1, state_size=poem_factor, retain_original=False)
    other_model = markovify.Text(text2, state_size=poem_factor, retain_original=True)
    model = markovify.combine([crimso_model, other_model], [1, 2])

    output_poem = []  # type: List[str]
    for _ in range(number_lines):
        outline = None
        while outline is None:
            outline = model.make_short_sentence(80)
        output_poem.append(outline)

    return '\n'.join(output_poem)


def wisdom() -> str:
    """Wisdom."""

    with open(c.clib_path_join('text', 'wisdom.txt'), encoding='utf8', errors='ignore') as f:
        text = f.read()

    factor = 3
    model = markovify.Text(text, state_size=factor)

    output = None
    while output is None:
        output = model.make_short_sentence(300)

    return output


def rovin() -> str:
    """Wisdom."""

    with open(c.clib_path_join('text', 'rovin.txt'), encoding='utf8', errors='ignore') as f:
        text = f.read()
    f.close()

    factor = 3
    model = markovify.Text(text, state_size=factor)

    output = []  # type: List[str]
    while len(output) < 5:
        output.append(model.make_short_sentence(300))

    return ' '.join(output)


def crimso() -> str:
    """Generates crimsonic text."""

    with open(c.clib_path_join('text', 'crimso.txt'), encoding='utf8', errors='ignore') as f:
        text = f.read()

    factor = 2
    model = markovify.NewlineText(text, state_size=factor, retain_original=False)

    output = None
    while output is None:
        output = model.make_sentence()

    return output


async def async_wrap(bot: Bot, func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Wraps a sync function into an asynchronous executor. Useful everywhere but it's here just because."""

    func = functools.partial(func, *args, **kwargs)
    output = await bot.loop.run_in_executor(None, func)

    return output

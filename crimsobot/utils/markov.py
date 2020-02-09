import functools
import random as r
import re
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


def clean_text(text: str) -> str:
    """Clean text for Markov corpus."""

    text = text.upper()
    text = re.sub(r"[^A-Z0-9 .,?!\-']+", ' ', text)
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')

    return text


def learner(msg: str) -> None:
    with open(c.clib_path_join('text', 'crimso.txt'), 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % msg)


def scraper(msg: str) -> None:
    with open(c.clib_path_join('text', 'scrape.txt'), 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % msg)


def scatter(msg_list: List[str]) -> str:
    """Write text file from list of strings."""

    with open(c.clib_path_join('text', 'scatterbrain.txt'), 'w', encoding='utf8', errors='ignore') as f:
        for item in msg_list:
            if not item.startswith('>'):
                if not item.startswith('?'):
                    f.write('%s\n' % item)

    g = open(c.clib_path_join('text', 'scatterbrain.txt'), 'r', encoding='utf8', errors='ignore')
    li = g.read()
    g.close()

    # Note: listifying file() leaves \n at end of each list element
    st = ''.join(li)
    # comment out next line to get case-sensitive version
    st = st.lower()
    se = set(st.split('\n'))
    text = '\n'.join(sorted(se))

    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    text = text.upper()

    factor = 1

    model = markovify.Text(text, state_size=factor)
    out = None
    while out is None:
        out = model.make_short_sentence(r.randint(40, 400))

    return out


def poem(number_lines: int) -> str:
    """Write a poem."""

    g = open(c.clib_path_join('text', 'all.txt'), encoding='utf8', errors='ignore')
    text1 = g.read()
    g.close()
    text1 = clean_text(text1)

    h = open(c.clib_path_join('text', 'randoms.txt'), encoding='utf8', errors='ignore')
    text2 = h.read()
    h.close()
    text2 = clean_text(text2)

    poem_factor = 2

    crimso_model = markovify.Text(text1, state_size=poem_factor)
    other_model = markovify.Text(text2, state_size=poem_factor)
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

    f = open(c.clib_path_join('text', 'wisdom.txt'), encoding='utf8', errors='ignore')
    text = f.read()
    f.close()

    factor = 3
    model = markovify.Text(text, state_size=factor)

    output = None
    while output is None:
        output = model.make_short_sentence(300)

    return output


def rovin() -> str:
    """Wisdom."""

    f = open(c.clib_path_join('text', 'rovin.txt'), encoding='utf8', errors='ignore')
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

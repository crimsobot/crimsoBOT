import asyncio
import functools
import random as r
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union

import markovify
from discord.ext import tasks
from discord.ext.commands import Bot, Context

from crimsobot.utils import tools as c


class CachedMarkov:

    def __init__(
        self,
        path: Union[str, List[str]],
        model_type: Type[markovify.Text],
        *args: Any,
        combine_weights: Optional[List[int]] = None,
        **kwargs: Any
    ) -> None:
        self.stale = True
        self._combine_weights = combine_weights
        self._model: Type[markovify.Text]
        self._model_type = model_type
        self._model_args = args
        self._model_kwargs = kwargs
        self._path = path

    @c.executor_function
    def build(self) -> None:
        self.stale = False  # We're updating the model, so it's no longer stale
        # If path is a single string, then only one model is being constructed - no combination is needed.
        if isinstance(self._path, str):
            with open(self._path, encoding='utf-8', errors='ignore') as text_file:
                text = text_file.read()

            self._model = self._model_type(text, *self._model_args, **self._model_kwargs)
            self._model.compile(inplace=True)

            return None

        # Path is a list of strings. Multiple paths = multiple models, which we'll create, combine, and then compile.
        models = []  # type: List[markovify.Text]
        for path in self._path:
            with open(path, encoding='utf-8', errors='ignore') as text_file:
                models.append(self._model_type(text_file.read(), *self._model_args, **self._model_kwargs))

        self._model = markovify.combine(models, self._combine_weights)
        self._model.compile(inplace=True)

    @c.executor_function
    def make_sentence(self, init_state: Optional[Any] = None, **kwargs: Any) -> Any:
        return self._model.make_sentence(init_state, **kwargs)

    @c.executor_function
    def make_short_sentence(self,  max_chars: int, min_chars: int = 0, **kwargs: Any) -> Any:
        return self._model.make_short_sentence(max_chars, min_chars, **kwargs)

    @c.executor_function
    def make_sentence_with_start(self, beginning: str, strict: bool = True, **kwargs: Any) -> Any:
        return self._model.make_sentence_with_start(beginning, strict, **kwargs)


@tasks.loop(minutes=10)
async def update_models(bot: Bot) -> None:
    for model in bot.markov_cache.values():
        if model.stale:
            await model.build()


def learner(msg: str) -> None:
    with open(c.clib_path_join('text', 'crimso.txt'), 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % msg)


def scraper(msg: str) -> None:
    with open(c.clib_path_join('text', 'scrape.txt'), 'a', encoding='utf8', errors='ignore') as f:
        f.write('%s\n' % msg)


@c.executor_function
def scatter(msg_list: List[str]) -> str:
    """Write text file from list of strings."""

    one_long_string = '\n'.join(msg_list)
    one_long_string = one_long_string.upper()

    model = markovify.NewlineText(one_long_string, state_size=1)

    # sometimes this process will fail to make a new sentence if the corpus is too short or lacks variety.
    # so I let it try for 8 seconds to do the thing, but kill it after that.
    now = time.time()
    out = None  # type: Optional[str]
    while time.time() < now + 5:
        if not out:
            out = model.make_short_sentence(r.randint(40, 400))
            if out:
                break

    if not out:
        out = 'NO.'

    return out


async def poem(ctx: Context, number_lines: int) -> str:
    """Write a poem."""

    output_poem = []  # type: List[str]
    for _ in range(number_lines):
        outline = None
        while outline is None:
            outline = await ctx.bot.markov_cache['poem'].make_short_sentence(80)
        output_poem.append(outline)

    return '\n'.join(output_poem)


async def wisdom(ctx: Context) -> str:
    """Wisdom."""

    output = None
    while output is None:
        output = await ctx.bot.markov_cache['wisdom'].make_short_sentence(300)

    return output


async def rovin(ctx: Context) -> str:
    """Wisdom."""

    output = []  # type: List[str]
    while len(output) < 5:
        output.append(await ctx.bot.markov_cache['rovin'].make_short_sentence(300))

    return ' '.join(output)


async def crimso(ctx: Context) -> str:
    """Generates crimsonic text."""

    output = None
    while output is None:
        output = await ctx.bot.markov_cache['crimso'].make_sentence()

    return output


async def async_wrap(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Wraps a sync function into an asynchronous executor. Useful everywhere but it's here just because."""

    loop = asyncio.get_event_loop()
    func = functools.partial(func, *args, **kwargs)

    return await loop.run_in_executor(None, func)


async def initialize_markov() -> Dict[str, CachedMarkov]:
    cache = {
        'crimso': CachedMarkov(
            c.clib_path_join('text', 'crimso.txt'),
            markovify.NewlineText,
            state_size=2,
            retain_original=False
        ),
        'rovin': CachedMarkov(
            c.clib_path_join('text', 'rovin.txt'),
            markovify.Text,
            state_size=3
        ),
        'wisdom': CachedMarkov(
            c.clib_path_join('text', 'wisdom.txt'),
            markovify.Text,
            state_size=3,
        ),
        'poem': CachedMarkov(
            [c.clib_path_join('text', 'all.txt'), c.clib_path_join('text', 'randoms.txt')],
            markovify.Text,
            combine_weights=[1, 2],
            state_size=2,
            retain_original=False
        ),
    }

    return cache

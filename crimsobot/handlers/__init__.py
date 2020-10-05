import asyncio
from typing import Any, Awaitable, Callable, Mapping, Tuple, Type, TypeVar, Union

from discord.ext.commands import Context

from crimsobot.exceptions import StopHandler


def _wrap(func: Callable) -> Callable[..., Awaitable]:
    async def inner(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(self, *args, **kwargs)
        except StopHandler:
            self._underlying_task.cancel()

    return inner


T = TypeVar('T', bound='AbstractEventGatherer')


# This is a helper decorator that can be used on AbstractEventGatherer subclasses. It allows you to enforce a
# subclass receiving only a specific type of event without editing attributes or overriding functions yourself.
def must_be_event(*event_names: str) -> Callable:
    def inner(cls: Type[T]) -> Type[T]:
        if not issubclass(cls, AbstractEventGatherer):
            raise TypeError('Decorated class must derive from AbstractEventGatherer!')
        # Ignored because Mypy is confused. It thinks that this can be Tuple[str, ...]
        cls._bound_event = event_names[0] if len(event_names) == 1 else event_names  # type: ignore
        return cls

    return inner


# You are very likely thinking "oh god oh fuck what is this wizardry" right about now. Let me explain.
# A metaclass allows us to manipulate user-defined subclasses with our own behavior.
# In this case, we wrap the event functions so that the user can raise StopHandler in any event function to
# stop handling immediately and return to the caller, without waiting for the timeout.
# Think of it as a cheat-y way to decorate a user-defined class /without/ them actually doing anything.
class EventGathererMeta(type):
    # I have no cloue how to type-hint a metaclass. It doesn't affect anything so it's no big deal.
    def __new__(cls, name, bases, attrs):  # type: ignore
        attrs['on_attach'] = _wrap(attrs['on_attach'])
        attrs['on_event'] = _wrap(attrs['on_event'])

        return super(EventGathererMeta, cls).__new__(cls, name, bases, attrs)  # type: ignore


class AbstractEventGatherer(metaclass=EventGathererMeta):
    # This is cheating, but hey, it works. See the following for an explanation:
    # https://github.com/python/cpython/blob/master/Lib/asyncio/coroutines.py#L161
    # https://github.com/python/cpython/blob/master/Lib/asyncio/coroutines.py#L167
    # Mypy is lying.
    _is_coroutine = asyncio.coroutines._is_coroutine  # type: ignore
    _bound_event: Union[None, str, Tuple[str]] = None

    def __init__(self, context: Context, *, timeout: float) -> None:
        self.context = context
        self.bot = context.bot  # ease of use
        # Mypy loves to lie.
        self._underlying_task = asyncio.create_task(asyncio.sleep(timeout))  # type: ignore
        self._attach_args: Tuple = tuple()
        self._attach_kwargs: Mapping[str, Any] = {}

    async def __call__(self, *args: Any) -> None:
        if len(args) == 1:
            await self.on_event(args[0])
        else:
            await self.on_event(*args)

    def set_arguments(self, *args: Any, **kwargs: Any) -> None:
        """Sets the arguments that will be passed to on_attach"""

        self._attach_args = args
        self._attach_kwargs = kwargs

    async def on_attach(self, *args: Any, **kwargs: Any) -> None:
        """Called before the gatherer is added as a listener. You can set the arguments that this function recives with
        ~AbstractEventGatherer.set_arguments(). By default, no arguments are provided.
        """

        pass

    async def on_event(self, *args: Any) -> None:
        """Called when the event that we are listening for is received. This function receives the arguments dispatched
        with the event, i.e if we are listening for on_message, this function will receive a message argument, but
        if we are listening for on_reaction_add, this function will receive both a reaction and user argument.
        If need be, an AbstractEventGatherer subclass can be decorated with the @must_be_event() decorator to
        ensure that it only receives certain event types.
        """

        pass

    async def on_detach(self) -> None:
        """Called when the gatherer is removed as a listener. Receives no arguments. Intended to be used as
        asynchronous cleanup.
        """

        pass

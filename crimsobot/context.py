import asyncio
from typing import TypeVar

from discord.ext.commands import Context

from crimsobot.handlers import AbstractEventGatherer


# "bound" param indicates that T must derive from AbstractEventGatherer
T = TypeVar('T', bound=AbstractEventGatherer)


class CrimsoContext(Context):
    async def gather_events(self, event_name: str, *, handler: T) -> T:
        bound_event = handler.__class__._bound_event
        if bound_event:
            string_enforced = isinstance(bound_event, str) and bound_event == event_name
            tuple_enforced = isinstance(bound_event, tuple) and event_name in bound_event
            if not (string_enforced or tuple_enforced):
                allowed = ', '.join(bound_event) if isinstance(bound_event, tuple) else bound_event
                raise ValueError(f'Handler {handler.__class__} is only compatible with {allowed}')

        # This is called here to prevent a race condition where an overridden on_event could require state that is
        # constructed in on_attach, even though it would make more sense for on_event to be called after add_listener.
        await handler.on_attach(*handler._attach_args, **handler._attach_kwargs)
        self.bot.add_listener(handler, event_name)
        # The handler either completed normally, or StopHandler was raised and cancelled it (causing the error) so that
        # it stopped early. Since the task is cancelled properly at this point, it's fine to swallow this error -
        # there's no use in allowing it to propagate.
        try:
            await handler._underlying_task
        except asyncio.CancelledError:
            pass
        finally:
            self.bot.remove_listener(handler, event_name)
            await handler.on_detach()

        # Remember to phone home
        return handler

from typing import Any, List, Mapping

from discord.ext.commands import Command, Context, DefaultHelpCommand
from discord.ext.menus import CannotAddReactions, CannotReadMessageHistory, ListPageSource, Menu, MenuPages


# This is a function because it is an utter mess inline
def _right_replace(relevant_string: str, to_replace: str, replace_with: str, times: int) -> str:
    return replace_with.join(relevant_string.rsplit(to_replace, times))


class HelpCommandPageSource(ListPageSource):

    def __init__(self, data: List[Any], ending_note: str) -> None:
        super().__init__(data, per_page=1)
        self.ending_note = ending_note

    async def format_page(self, menu: Menu, page: Any) -> str:
        if menu.current_page + 1 == len(self.entries):  # Last page
            # Get rid of the ending note here - it'll be added below the body.
            page = _right_replace(page, '\n\n' + self.ending_note, '', 1)

        to_send = f'{page}```fix\n{self.ending_note}```'

        return to_send


class PaginatedHelpCommand(DefaultHelpCommand):

    async def prepare_help_command(self, ctx: Context, command: Command) -> None:
        # Some explanation for this:
        # Some commands have extremely long docstrings, and will trigger the paginator. Since this is unwanted
        # behavior, we keep track of how the command is being invoked so that if a plain >help is used, the paginator
        # will run, but won't run for any other form of the help command.
        self.paginator.clear()
        self.bot_help_invocation = False

    async def send_bot_help(self, mapping: Mapping) -> None:
        self.bot_help_invocation = True
        await super().send_bot_help(mapping)

    async def send_pages(self) -> Any:
        # This method is overriden so that we can use our own pagination approach.
        # While we could use self.context here (instead of this destination mess), it's best to respect the
        # configuration options that we have available - the help command can be configured to DM users depending on
        # page length, and we don't want to break that behavior needlessly.
        destination = self.get_destination()
        if not self.bot_help_invocation:
            return await super().send_pages()

        # This was called with a plain >help, so we can run the fancy paginator.
        destination_as_messageable = destination.channel if isinstance(destination, Context) else destination
        source = HelpCommandPageSource(self.paginator.pages, self.get_ending_note())
        menu = MenuPages(source, timeout=180, clear_reactions_after=True)

        try:
            await menu.start(self.context, channel=destination_as_messageable, wait=True)
        except (CannotAddReactions, CannotReadMessageHistory):
            # We can't paginate due to permissions - fall back to default behavior
            await super().send_pages()

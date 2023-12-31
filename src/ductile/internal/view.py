from typing import TYPE_CHECKING

from discord import ui

if TYPE_CHECKING:
    from discord import Interaction

    from ..types import ViewErrorHandler, ViewTimeoutHandler  # noqa: TID252

__all__ = [
    "_InternalView",
]


class _InternalView(ui.View):
    def __init__(
        self,
        *,
        timeout: float | None = 180,
        on_error: "ViewErrorHandler | None" = None,
        on_timeout: "ViewTimeoutHandler | None" = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.__on_error = on_error
        self.__on_timeout = on_timeout

    async def on_error(self, interaction: "Interaction", error: Exception, item: ui.Item) -> None:
        if self.__on_error:
            await self.__on_error(interaction, error, item)

        await super().on_error(interaction, error, item)

    async def on_timeout(self) -> None:
        if self.__on_timeout:
            await self.__on_timeout()

        await super().on_timeout()

from typing import TYPE_CHECKING, Any, Literal, NamedTuple, overload

from ..internal import _InternalView  # noqa: TID252
from ..state import State  # noqa: TID252
from ..utils import wait_tasks_by_name  # noqa: TID252

if TYPE_CHECKING:
    from collections.abc import Generator

    from discord import Message

    from ..view import View, ViewObject  # noqa: TID252
    from .type import ViewObjectDictWithAttachment, ViewObjectDictWithFiles


class ViewResult(NamedTuple):
    """
    ViewResult is a named tuple representing the result of the view.

    Parameters
    ----------
    NamedTuple : `ViewResult`
        The result of the view.
    """

    timed_out: bool
    states: dict[str, Any]


class ViewController:
    """ViewController is a class that controls the view."""

    def __init__(self, view: "View", *, timeout: float | None = 180) -> None:
        self.__view = view
        view._controller = self  # noqa: SLF001
        self.__raw_view = _InternalView(timeout=timeout, on_error=self.__view.on_error, on_timeout=self.__view.on_timeout)
        self.__message: "Message | None" = None

    @property
    def message(self) -> "Message | None":
        """
        return attached message with the View.

        Returns
        -------
        `discord.Message | None`
            The attached message. None if the View is not sent yet.
        """
        return self.__message

    @message.setter
    def message(self, value: "Message | None") -> None:
        self.__message = value

    async def send(self) -> None:
        """
        Send the view to the channel.

        Raises
        ------
        NotImplementedError
            If this method is not implemented in subclasses.
        """
        # implement this in subclasses
        raise NotImplementedError

    async def sync(self) -> None:
        """Sync the message with current view."""
        if self.message is None:
            return

        # maybe validation for self.__view is needed
        d = self._process_view_for_discord("attachment")
        self.message = await self.message.edit(**d)

    def stop(self) -> None:
        """Stop the view and return the state of all states in the view."""
        self.__raw_view.stop()

    async def wait(self) -> ViewResult:
        """
        Wait for the view to stop and return the state of all states in the view.

        Returns
        -------
        `ViewResult(NamedTuple)`
            The result of the view.

            `timed_out` is True if the view timed out and False otherwise. same as `discord.ui.View.wait`.

            `states` is a dictionary of all states in the view.
        """
        is_timed_out = await self.__raw_view.wait()

        if is_timed_out:
            # this is got from discord.ui.View._dispatch_timeout()
            timeout_task_name = f"discord-ui-view-timeout-{self.__raw_view.id}"
            await wait_tasks_by_name([timeout_task_name])

        d = {}
        for key, state in self._get_all_state_in_view():
            d[key] = state.get_state()
        return ViewResult(is_timed_out, d)

    def _get_all_state_in_view(self) -> "Generator[tuple[str, State[Any]], None, None]":
        for k, v in self.__view.__dict__.items():
            if isinstance(v, State):
                yield k, v

    @overload
    def _process_view_for_discord(self, mode: Literal["attachment"]) -> "ViewObjectDictWithAttachment": ...

    @overload
    def _process_view_for_discord(self, mode: Literal["files"]) -> "ViewObjectDictWithFiles": ...

    def _process_view_for_discord(
        self,
        mode: Literal["attachment", "files"],
    ) -> "ViewObjectDictWithAttachment | ViewObjectDictWithFiles":
        """
        _process_view_for_discord is a helper function to process the view for Discord.

        Parameters
        ----------
        mode : Literal[&quot;attachment&quot;, &quot;files&quot;]
            The mode to process the view for Discord.

            If the mode is `attachment`, ViewObject.files will be put into the `attachments` key.

            If the mode is `files`, ViewObject.files will be put into the `files` key.

        Returns
        -------
        ViewObjectDictWithAttachment | ViewObjectDictWithFiles
            The processed view dictionary.
            This can be passed to `discord.abc.Messageable.send` or `discord.abc.Messageable.edit` and etc
            as unpacked keyword arguments.
        """
        view_object: "ViewObject" = self.__view.render()

        # implicitly clear view every time see:#54
        v = self.__raw_view
        v.clear_items()
        if view_object.components:
            for child in view_object.components:
                v.add_item(child)

        if mode == "attachment":
            # implicitly clear items every time see:#54

            return {
                "content": view_object.content,
                "embeds": view_object.embeds or [],
                "view": v,
                "attachments": view_object.files or [],
            }

        return {
            "content": view_object.content,
            "embeds": view_object.embeds or [],
            "view": v,
            "files": view_object.files or [],
        }

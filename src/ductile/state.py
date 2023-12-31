import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from .utils import get_logger

if TYPE_CHECKING:
    from .view import View

T = TypeVar("T", bound=Any)

__all__ = [
    "State",
    # "use_state",
]


class State(Generic[T]):
    """
    A class representing a state with a generic type T.

    Methods
    -------
    __call__() -> `T`:
        Return the current value of the state.
    get_state() -> `T`:
        Return the current value of the state.
    set_state(new_value: `T | Callable[[T], T]`) -> `None`:
        Set the current value of the state to the new value.
    """

    def __init__(self, initial_value: T, view: "View", /, *, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self.__initial_value: T = initial_value
        self.__current_value: T = initial_value
        self.__previous_value: T | None = None

        self._loop = loop or asyncio.get_event_loop()
        self._view = view
        self._logger = get_logger(self.__class__.__name__)

    def __call__(self) -> T:
        """
        Return the current value of the state. equivalent to `State.get_state()`.

        Returns
        -------
        `T`
            The current value of the state.
        """
        return self.get_state()

    @property
    def _current_value(self) -> T:
        """
        property: The current value of the state.

        Returns
        -------
        T
            The current value of the state.
        """
        return self.__current_value

    @_current_value.setter
    def _current_value(self, new_value: T) -> None:
        """
        Set the current value of the state to the new value.

        This method automatically sets the previous value of the state to the current value of the state.

        Parameters
        ----------
        new_value : T
            The new value of the state.
        """
        self.__previous_value = self.__current_value
        self.__current_value = new_value

    def get_state(self) -> T:
        """
        Return the current value of the state.

        Returns
        -------
        `T`
            The current value of the state.
        """
        return self._current_value

    def set_state(self, new_value: T | Callable[[T], T]) -> None:
        """
        Set the current value of the state to the new value.

        After the state is changed, this method calls `View.sync()` to synchronize the view with the controller.

        Parameters
        ----------
        new_value : `T | Callable[[T], T]`
            The new value of the state. If the type is `Callable[[T], T]`, the callable is called with the current
            value of the state and the return value is used as the new value of the state.
        """
        _new_value: T = self._current_value

        if isinstance(new_value, Callable):
            try:
                r = new_value(self._current_value)
            except Exception:
                self._logger.exception("Error while executing callable")
            else:
                if not isinstance(r, type(self._current_value)):
                    self._logger.warning("Callable returned value of different type")
                else:
                    _new_value = r
        else:
            _new_value = new_value

        msg = f"State changed: {self._current_value} -> {_new_value}"
        self._logger.debug(msg)
        self._current_value = _new_value
        self.__sync()

    def revert_state(self) -> None:
        """
        Revert the current value of the state to the previous value.

        After the state is changed, this method calls `View.sync()` to synchronize the view with the controller.
        """
        if self.__previous_value is not None:
            self._current_value = self.__previous_value
            self.__sync()
        else:
            self._logger.warning("No previous value")

    def __sync(self) -> None:
        if self._view:
            self._view.sync()
        else:
            self._logger.warning("View is not set")


# class UseStateTuple(NamedTuple, Generic[T]):
#     state: State[T]
#     set_state: Callable[[T | Callable[[T], T]], None]


# def use_state(
#     initial_value: T,
#     view: "View",
#     /,
#     *,
#     loop: asyncio.AbstractEventLoop | None = None,
# ) -> UseStateTuple[T]:
#     s = State[T](initial_value, view, loop=loop)
#     return UseStateTuple(state=s, set_state=s.set_state)

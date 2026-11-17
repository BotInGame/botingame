"""Game contract: every game is a pure, deterministic state machine.

The platform never knows game rules; it only calls these methods. This keeps
adding a new game to "write one class + register it".
"""
from abc import ABC, abstractmethod
from typing import Any, Literal


SpectatingPolicy = Literal["public", "delayed", "post-match"]


class IllegalMove(ValueError):
    pass


class Game(ABC):
    id: str
    name: str
    version: str
    players: int = 2
    rules: str = ""
    spectating_policy: SpectatingPolicy = "public"
    spectating_delay_turns: int | None = None  # "delayed" policy only: how many turns behind Spectators watch
    default_move_timeout_s: float = 20
    move_schema: dict
    view_schema: dict

    @abstractmethod
    def initial_state(self, seed: int) -> dict[str, Any]: ...

    @abstractmethod
    def to_move(self, state: dict) -> set[int]:
        """Seats expected to move; empty once the Match is over."""

    @abstractmethod
    def legal_moves(self, state: dict, seat: int) -> list[Any]: ...

    @abstractmethod
    def apply(self, state: dict, seat: int, move: Any) -> dict:
        """Return a new state. Raise IllegalMove on invalid input."""

    @abstractmethod
    def outcome(self, state: dict) -> list[float] | None:
        """Score per seat once finished (1 win, 0.5 draw, 0 loss), else None."""

    def view(self, state: dict, seat: int | None) -> dict:
        """What a seat (None = the Public view) may see: the full state minus its seed.

        Override for hidden information; the Public view must stay within every seat's view.
        """
        return {k: v for k, v in state.items() if k != "seed"}

    def public_move(self, state: dict, seat: int, move: Any) -> Any:
        """`move`, played by `seat` in `state`, as a Spectator may see it live under the `post-match` policy
        (by default, as played; `delayed` shows nothing of a move until its delay has passed). Override to hide
        what the Public view hides: two moves that leave the same Public view must give the same public move."""
        return move

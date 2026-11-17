from .base import Game, IllegalMove
from .battleship import Battleship
from .connect4 import ConnectFour
from .dots import DotsAndBoxes
from .uttt import UltimateTicTacToe

# Ultimate Tic-tac-toe first: the hello-world Game the Quickstart and lists lead with.
GAMES: dict[str, Game] = {g.id: g for g in (UltimateTicTacToe(), ConnectFour(), DotsAndBoxes(), Battleship())}



def game_info(g: Game) -> dict:
    """A Game as the Bot API serves it (`GET /v1/games/{id}`), with an example: the seat to move first in a new
    Match (seed 0), its view and its first legal move."""
    state = g.initial_state(seed=0)
    seat = min(g.to_move(state))
    return {"id": g.id, "name": g.name, "version": g.version, "players": g.players, "rules": g.rules,
            "spectating_policy": g.spectating_policy, "default_move_timeout_s": g.default_move_timeout_s,
            "move_schema": g.move_schema, "view_schema": g.view_schema,
            "example_seat": seat, "example_move": g.legal_moves(state, seat)[0], "example_view": g.view(state, seat)}


__all__ = ["GAMES", "Game", "IllegalMove", "game_info"]

"""The inline Game menu that `botingame games` browses and `botingame new` picks from, driven through a pipe as a
terminal would type into it."""
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from botingame.games import GAMES, game_info
from botingame.cli.menu import browse, pick_game

ROWS = [game_info(g) for g in GAMES.values()]  # uttt, connect4, dots, battleship
DOWN, UP, RIGHT, ENTER, ESC = "\x1b[B", "\x1b[A", "\x1b[C", "\r", "\x1b"


def pick(keys: str, **kw):
    with create_pipe_input() as pipe:
        pipe.send_text(keys)
        return pick_game(ROWS, input=pipe, output=DummyOutput(), **kw)


def test_enter_picks_the_selected_game():
    assert pick(ENTER) == "uttt"
    assert pick(DOWN + DOWN + ENTER) == "dots"


def test_j_k_move_and_right_picks():
    assert pick("j" + "j" + "k" + RIGHT) == "connect4"
    assert pick(DOWN + UP + ENTER) == "uttt"


def test_q_and_escape_quit_without_a_game():
    assert pick("q") is None
    assert pick(ESC) is None


def test_the_menu_starts_on_the_default_game():
    assert pick(ENTER, default="battleship") == "battleship"


def test_browse_opens_each_picked_game_and_comes_back_to_it():
    opened, defaults = [], []
    answers = iter(["dots", "dots", "connect4", None])  # the developer opens dots twice, then connect4, then quits

    def fake_pick(rows, default=None, action="pick"):
        defaults.append((default, action))
        return next(answers)
    browse(ROWS, opened.append, pick=fake_pick)
    assert opened == ["dots", "dots", "connect4"]
    assert defaults == [(None, "open"), ("dots", "open"), ("dots", "open"), ("connect4", "open")]  # back on it

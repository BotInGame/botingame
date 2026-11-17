"""The `botingame` CLI offline. Its online commands (`run`, and `games` and `game` without `--offline`) are tested
against the Bot API by the platform."""
import io
import re
from types import SimpleNamespace

import pytest
from rich.console import Console
from rich.pager import Pager
from typer.testing import CliRunner

import botingame
from botingame.cli import app
from botingame.cli.commands import print_guide
from botingame.games import GAMES
from botingame.docs import guide

runner = CliRunner()


@pytest.fixture(autouse=True)
def _no_platform(monkeypatch):
    """No test here reaches the real platform: the Bot API's and the web app's URLs point where nothing listens. And
    `--help` prints plain text, as on a pipe, even on GitHub Actions, where Typer would force colour codes into it."""
    monkeypatch.setattr("typer.rich_utils.FORCE_TERMINAL", False)
    monkeypatch.setenv("BOTINGAME_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("BOTINGAME_WEB_URL", "http://127.0.0.1:9")


def cli(*args, input=None):
    return runner.invoke(app, list(args), input=input)


def test_version_prints_the_version_first_then_the_legal_notices():
    r = cli("--version")
    assert r.exit_code == 0
    assert r.output == (f"botingame {botingame.__version__}\n"
                        "Based on botingame by BotInGame (https://github.com/BotInGame/botingame)\n"
                        "Copyright (C) 2026 BotInGame. Free software under GPL-3.0-or-later;\n"
                        "you may redistribute it under its terms. There is NO WARRANTY.\n")


def test_help_lists_version_as_printing_the_legal_notices():
    unwrapped = " ".join(cli("--help").output.replace("│", " ").split())
    assert "--version Print the version, copyright and licence notices." in unwrapped


@pytest.fixture
def on_terminal(monkeypatch):
    """As if `botingame` ran in a terminal: the Game menus it opens are recorded in `.opened` (their arguments), and
    return `.picked`."""
    terminal = SimpleNamespace(opened=[], picked=None)

    def show_menu(rows, load_page=None):
        terminal.opened.append((rows, load_page))
        return terminal.picked
    monkeypatch.setattr("botingame.cli.commands.on_terminal", lambda menu=False: True)
    monkeypatch.setattr("botingame.cli.commands.show_menu", show_menu)
    return terminal


GAME_ROWS = [("uttt", "Ultimate Tic-tac-toe"), ("connect4", "Connect Four"), ("dots", "Dots and Boxes"),
             ("battleship", "Battleship")]


@pytest.mark.parametrize("plain", [[], ["--plain"]])
def test_games_offline_prints_a_table_of_every_installed_game(plain):
    r = cli("games", "--offline", *plain)
    assert r.exit_code == 0
    assert "Bot API" not in r.output  # offline: no health header
    assert re.search(r"^Key\s+Name\s+Players\s+Version\s*$", r.output, re.M), r.output
    for key, name in GAME_ROWS:
        assert re.search(rf"^{key}\s+{name}\s+2\s+1\.0\.0\s*$", r.output, re.M), r.output
    assert "Move =" not in r.output  # no rules: `botingame game <key>` has them
    assert "\x1b[" not in r.output  # not a terminal: no styling


def test_games_on_a_terminal_opens_the_menu_on_each_games_installed_guide(on_terminal):
    r = cli("games", "--offline")
    assert r.exit_code == 0, r.output
    [(rows, load_page)] = on_terminal.opened
    assert [g["id"] for g in rows] == [key for key, _ in GAME_ROWS]
    assert load_page("dots") == guide(GAMES["dots"])  # a page shows what `botingame game dots` shows


def test_games_plain_prints_the_table_even_on_a_terminal(on_terminal):
    r = cli("games", "--offline", "--plain")
    assert r.exit_code == 0 and on_terminal.opened == [] and "Connect Four" in r.output


@pytest.mark.parametrize("key", list(GAMES))
def test_game_offline_prints_the_installed_english_guide_as_plain_markdown_when_not_on_a_terminal(key):
    r = cli("game", key, "--offline")
    assert r.exit_code == 0, r.output
    assert r.output == guide(GAMES[key], "en") + "\n"  # the Markdown source: no styling, no pager, no health header


def test_no_pager_prints_the_guide_straight():
    r = cli("game", "connect4", "--offline", "--no-pager")
    assert r.exit_code == 0 and r.output.startswith("# Connect Four")


class RecordingPager(Pager):
    def __init__(self):
        self.shown: list[str] = []

    def show(self, content: str) -> None:
        self.shown.append(content)


def terminal(height: int) -> Console:
    return Console(file=io.StringIO(), force_terminal=True, width=100, height=height)


def test_on_a_terminal_the_guide_is_rendered_and_paged_when_taller_than_the_terminal():
    console, pager = terminal(height=20), RecordingPager()
    print_guide(guide(GAMES["uttt"]), console=console, pager=pager)
    assert len(pager.shown) == 1 and console.file.getvalue() == ""
    shown = pager.shown[0]
    assert "\x1b[" in shown  # styled
    assert "# Ultimate" not in shown and "Ultimate Tic-tac-toe" in shown  # rendered, not the Markdown source
    assert "Field" in shown and "cells" in shown  # the view's table


def test_on_a_terminal_a_short_guide_or_no_pager_prints_straight():
    for console, kw in [(terminal(height=10_000), {}), (terminal(height=20), {"use_pager": False})]:
        pager = RecordingPager()
        print_guide(guide(GAMES["uttt"]), console=console, pager=pager, **kw)
        assert pager.shown == [] and "Ultimate Tic-tac-toe" in console.file.getvalue()


def test_help_describes_the_new_options_and_keys():
    games = cli("games", "--help").output
    assert "--plain" in games and "Enter" in games and "Esc" in games and "pager" in games
    assert "--step" in cli("play", "--help").output
    assert "arrow-key menu" in cli("new", "--help").output


def test_game_help_describes_the_guide_and_no_pager():
    r = cli("game", "--help")
    assert "guide" in r.output and "--no-pager" in r.output


def test_an_unknown_game_exits_non_zero_with_the_valid_keys():
    r = cli("game", "chess", "--offline")
    assert r.exit_code != 0
    assert "unknown Game 'chess'" in r.output and "uttt, connect4, dots, battleship" in r.output


@pytest.mark.parametrize("args", [["games"], ["game", "uttt"]])
def test_games_and_game_read_the_bot_api_and_say_so_when_it_is_unreachable(args):
    r = cli(*args, "--url", "http://127.0.0.1:9")  # nothing listens there
    assert r.exit_code != 0
    assert "cannot reach http://127.0.0.1:9" in r.output and "--offline" in r.output


SHORT_HELP = {"new": "Write a starter Bot and keep its token", "play": "Play Matches offline, to test a Bot",
              "run": "Play ranked Series on the platform", "games": "List the Games, and read their guides",
              "game": "Show a Game's technical guide", "health": "Check that the platform is up"}


def test_help_describes_every_command_in_one_whole_line_in_the_order_people_use_them():
    r = cli("--help")
    assert r.exit_code == 0
    for command, description in SHORT_HELP.items():
        assert re.search(rf"^│ +{command} +{description} +│$", r.output, re.M), (command, r.output)
    commands = r.output[r.output.index("Write a Bot"):]
    assert "..." not in commands and "…" not in commands  # nothing cut off
    assert "<bool>" not in cli("play", "--help").output  # an on/off flag shows no type
    assert [r.output.index(f"│ {c} ") for c in SHORT_HELP] == sorted(r.output.index(f"│ {c} ") for c in SHORT_HELP)
    for command in ("games", "game", "new", "play", "run", "health"):
        assert cli(command, "--help").exit_code == 0


def test_health_reports_a_service_down_and_exits_non_zero():
    r = cli("health")
    assert r.exit_code == 1
    assert re.search(r"Web app\s+● down\s+unreachable", r.output), r.output
    assert re.search(r"Bot API\s+● down\s+unreachable", r.output), r.output


FIRST_MOVE_BOT = '''
def choose_move(view, legal_moves):
    return legal_moves[0]
'''


@pytest.fixture
def first_bot(tmp_path):
    path = tmp_path / "first_bot.py"
    path.write_text(FIRST_MOVE_BOT)
    return str(path)


def tally(output):
    """(wins, losses, draws), from the tally table that ends `play`."""
    m = re.search(r"^ *Matches +Wins +Losses +Draws *\n *(\d+) +(\d+) +(\d+) +(\d+) *$", output, re.M)
    assert m, output
    matches, *wins_losses_draws = map(int, m.groups())
    assert matches == sum(wins_losses_draws)
    return tuple(wins_losses_draws)


@pytest.mark.parametrize("key", list(GAMES))
def test_play_runs_offline_against_random(first_bot, key):
    r = cli("play", first_bot, "--game", key)
    assert r.exit_code == 0, r.output
    assert sum(tally(r.output)) == 1


@pytest.mark.parametrize("key", list(GAMES))
def test_play_against_another_bot_file(first_bot, tmp_path, key):
    other = tmp_path / "other.py"
    other.write_text("def choose_move(view, legal_moves):\n    return legal_moves[-1]\n")
    r = cli("play", first_bot, "--game", key, "--vs", str(other), "--matches", "2")
    assert r.exit_code == 0, r.output
    assert sum(tally(r.output)) == 2


def test_two_identical_bots_split_a_pair_of_matches_by_seat(first_bot):
    # Connect Four, both always playing column 0 then 1…: the first seat to move wins, and seats alternate.
    r = cli("play", first_bot, "--game", "connect4", "--vs", first_bot, "--matches", "4")
    assert tally(r.output) == (2, 2, 0)


def test_the_same_seed_gives_the_same_matches(first_bot):
    runs = [cli("play", first_bot, "--game", "uttt", "--matches", "5", "--seed", "7").output for _ in range(2)]
    assert runs[0] == runs[1]
    assert cli("play", first_bot, "--game", "uttt", "--matches", "5", "--seed", "8").output != runs[0]


def test_without_a_seed_play_prints_the_one_it_used(first_bot):
    r = cli("play", first_bot, "--game", "uttt")
    seed = re.search(r"--seed (\d+)", r.output).group(1)
    assert cli("play", first_bot, "--game", "uttt", "--seed", seed).output.splitlines()[1:] == r.output.splitlines()[1:]


BOARD_FOOTER = " 0 1 2 3 4 5 6"  # the column labels under each Connect Four board


def test_show_prints_the_board_after_every_move(first_bot):
    r = cli("play", first_bot, "--game", "connect4", "--seed", "1", "--show")
    moves = int(re.search(r"(\d+) moves", r.output).group(1))
    assert r.output.count(BOARD_FOOTER) == moves
    assert len(re.findall(r"^Move \d+: seat [01] plays \d$", r.output, re.M)) == moves


def test_step_plays_one_move_per_enter_and_shows_the_board_each_time(first_bot, on_terminal):
    r = cli("play", first_bot, "--game", "connect4", "--seed", "1", "--step", input="\n\n\nq\n")
    assert r.exit_code == 0, r.output
    assert r.output.count(BOARD_FOOTER) == 3  # three Enters, three moves, each with its board
    assert re.findall(r"^Move (\d+): seat [01] \((?:you|random)\) to play", r.output, re.M) == ["1", "2", "3", "4"]
    assert "Stopped" in r.output and tally(r.output) == (0, 0, 0)  # no Match finished


def test_step_plays_a_match_to_the_end_then_pauses_before_the_next(first_bot, on_terminal):
    r = cli("play", first_bot, "--game", "connect4", "--matches", "3", "--seed", "1", "--step",
            input="\n" * 200)  # far more Enters than one Match takes
    full = cli("play", first_bot, "--game", "connect4", "--matches", "3", "--seed", "1", "--show")
    first_match = int(re.search(r"Match 1 \(you: seat 0\): \w+, normal, (\d+) moves", full.output).group(1))
    stopped = cli("play", first_bot, "--game", "connect4", "--matches", "3", "--seed", "1", "--step",
                  input="\n" * first_match + "q\n")
    assert "Match 2 of 3: press Enter" in stopped.output
    assert sum(tally(stopped.output)) == 1  # the finished Match counts; the stop came before the second
    assert tally(r.output) == tally(full.output)  # stepping plays the same Matches


def test_step_stops_cleanly_when_its_input_ends(first_bot, on_terminal):
    r = cli("play", first_bot, "--game", "connect4", "--step", input="\n")
    assert r.exit_code == 0 and "Stopped" in r.output and tally(r.output) == (0, 0, 0)


def test_ctrl_c_during_a_step_run_stops_it_and_still_prints_the_tally(tmp_path, on_terminal):
    bot = tmp_path / "interrupted.py"  # as if Ctrl+C came while the Bot was thinking
    bot.write_text("def choose_move(view, legal_moves):\n    raise KeyboardInterrupt\n")
    r = cli("play", str(bot), "--game", "connect4", "--step", input="\n")
    assert r.exit_code == 0 and "Stopped" in r.output and tally(r.output) == (0, 0, 0)
    assert cli("play", str(bot), "--game", "connect4").exit_code != 0  # without --step, Ctrl+C aborts as before


def test_step_without_a_terminal_fails_clearly(first_bot):
    r = cli("play", first_bot, "--game", "connect4", "--step", input="\n" * 50)
    assert r.exit_code != 0 and "no terminal" in r.output and "--step" in r.output


def test_play_needs_a_game(first_bot):
    r = cli("play", first_bot)
    assert r.exit_code != 0 and "--game" in r.output


def test_an_illegal_move_loses_the_match(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def choose_move(view, legal_moves):\n    return 99\n")
    r = cli("play", str(bad), "--game", "connect4")
    assert tally(r.output) == (0, 1, 0) and "illegal move" in r.output


TOKEN = "big_s3cr3t-t0ken"


@pytest.fixture
def here(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def every_file_but_env(folder):
    return {p.name: p.read_text() for p in folder.rglob("*") if p.is_file() and p.name != ".env"}


def test_new_picks_the_game_from_the_menu_then_asks_the_path_and_a_hidden_token(here, on_terminal):
    on_terminal.picked = "connect4"
    r = cli("new", input=f"\n{TOKEN}\n")
    assert r.exit_code == 0, r.output
    [(rows, load_page)] = on_terminal.opened
    assert [g["id"] for g in rows] == list(GAMES) and load_page is None  # the menu as a picker
    assert "connect4_bot.py" in r.output  # the default path, offered
    assert TOKEN not in r.output  # typed hidden
    assert 'GAME = "connect4"' in (here / "connect4_bot.py").read_text()
    assert (here / ".env").read_text() == f"BOTINGAME_TOKEN={TOKEN}\n"


def test_quitting_the_menu_writes_nothing(here, on_terminal):
    r = cli("new")
    assert r.exit_code != 0 and "no Game picked" in r.output
    assert list(here.iterdir()) == []


@pytest.mark.parametrize("args, missing", [([], "--game"), (["--game", "uttt"], "--path"),
                                           (["--game", "uttt", "--path", "b.py"], "--token")])
def test_new_without_a_terminal_fails_instead_of_asking(here, args, missing):
    r = cli("new", *args, input="uttt\nb.py\n\n")
    assert r.exit_code != 0
    assert "no terminal" in r.output and missing in r.output
    assert list(here.iterdir()) == []


def test_new_ends_with_what_it_wrote_and_the_next_commands(here):
    r = cli("new", "--game", "dots", "--path", "b.py", "--token", TOKEN)
    assert r.exit_code == 0, r.output
    summary = r.output[r.output.index("b.py"):]
    for written in ("b.py", ".env", ".gitignore"):
        assert written in summary, written
    assert summary.index("botingame play b.py") < summary.index("botingame run b.py")  # test locally first


@pytest.mark.parametrize("key", list(GAMES))
def test_new_writes_a_bot_that_plays_to_the_end_of_a_match(here, key):
    r = cli("new", "--game", key, "--path", f"bots/{key}.py", "--token", "")
    assert r.exit_code == 0, r.output
    bot = (here / "bots" / f"{key}.py").read_text()
    assert "def choose_move(view, legal_moves):" in bot and f'GAME = "{key}"' in bot
    for field in GAMES[key].view_schema["required"]:
        assert f"`{field}`" in bot, field  # the comments describe the view
    played = cli("play", f"bots/{key}.py", "--matches", "2")
    assert played.exit_code == 0 and sum(tally(played.output)) == 2, played.output


def test_the_starter_bot_says_it_is_0bsd_on_its_first_line(here):
    assert cli("new", "--game", "uttt", "--path", "b.py", "--token", "").exit_code == 0
    assert (here / "b.py").read_text().splitlines()[0] == "# SPDX-License-Identifier: 0BSD"


def test_with_every_flag_new_asks_nothing(here):
    r = cli("new", "--game", "uttt", "--path", "b.py", "--token", TOKEN, input="")
    assert r.exit_code == 0, r.output
    assert not any(prompt in r.output for prompt in ("Game (number or key)", "Bot file", "Bot token"))
    assert (here / "b.py").exists()


def test_the_token_lands_only_in_env(here):
    (here / ".env").write_text("DEBUG=1\nBOTINGAME_TOKEN=big_old\nOTHER=x\n")
    (here / ".gitignore").write_text("__pycache__/\n")
    cli("new", "--game", "uttt", "--path", "b.py", "--token", TOKEN)
    assert (here / ".env").read_text() == f"DEBUG=1\nBOTINGAME_TOKEN={TOKEN}\nOTHER=x\n"
    assert all(TOKEN not in text for text in every_file_but_env(here).values())
    assert (here / ".gitignore").read_text() == "__pycache__/\n.env\n"


def test_env_and_gitignore_sit_next_to_the_bot_and_are_created_once(here):
    cli("new", "--game", "uttt", "--path", "sub/a.py", "--token", TOKEN)
    cli("new", "--game", "dots", "--path", "sub/b.py", "--token", "big_other")
    assert (here / "sub" / ".env").read_text() == "BOTINGAME_TOKEN=big_other\n"
    assert (here / "sub" / ".gitignore").read_text() == ".env\n"


def test_an_existing_env_without_a_token_line_gains_one(here):
    (here / ".env").write_text("DEBUG=1")  # no final newline
    cli("new", "--game", "uttt", "--path", "b.py", "--token", TOKEN)
    assert (here / ".env").read_text() == f"DEBUG=1\nBOTINGAME_TOKEN={TOKEN}\n"


def test_an_empty_token_writes_no_env(here):
    r = cli("new", "--game", "uttt", "--path", "b.py", "--token", "")
    assert r.exit_code == 0 and not (here / ".env").exists()
    assert "BOTINGAME_TOKEN" in r.output  # how to add it later


def test_new_never_overwrites_a_bot_file(here):
    (here / "b.py").write_text("# mine\n")
    r = cli("new", "--game", "uttt", "--path", "b.py", "--token", TOKEN)
    assert r.exit_code != 0 and "already exists" in r.output
    assert (here / "b.py").read_text() == "# mine\n" and not (here / ".env").exists()


def test_new_refuses_an_unknown_game(here):
    r = cli("new", "--game", "chess", "--path", "b.py", "--token", "")
    assert r.exit_code != 0 and not (here / "b.py").exists()


def test_run_without_a_token_exits_with_a_clear_message(here, first_bot, monkeypatch):
    monkeypatch.delenv("BOTINGAME_TOKEN", raising=False)
    r = cli("run", first_bot)
    assert r.exit_code != 0
    assert "no Bot token" in r.output and "--token" in r.output and "BOTINGAME_TOKEN" in r.output


def test_new_links_the_bot_to_the_installed_rules_when_the_platform_is_unreachable(here):
    r = cli("new", "--game", "uttt", "--path", "b.py", "--token", "")
    assert r.exit_code == 0, r.output
    assert f'GAME_VERSION = "{GAMES["uttt"].version}"' in (here / "b.py").read_text()
    assert "could not check the platform's uttt version" in r.output


def test_play_warns_when_the_bot_was_written_for_other_rules(tmp_path):
    bot = tmp_path / "old.py"
    bot.write_text('GAME = "uttt"\nGAME_VERSION = "0.9.0"\n' + FIRST_MOVE_BOT)
    r = cli("play", str(bot))
    assert r.exit_code == 0
    assert "your Bot was written for uttt 0.9.0, but these are the uttt 1.0.0 rules" in r.output
    newer = tmp_path / "newer.py"
    newer.write_text('GAME = "uttt"\nGAME_VERSION = "9.0.0"\n' + FIRST_MOVE_BOT)
    assert "your Bot was written for uttt 9.0.0, but your botingame" in cli("play", str(newer)).output


def test_play_says_nothing_about_versions_for_a_new_bot(here):
    cli("new", "--game", "connect4", "--path", "b.py", "--token", "")
    assert "Warning" not in cli("play", "b.py").output

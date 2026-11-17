"""The `botingame` command.

`games`, `game` and `run` read the Bot API, so they always show what the platform runs. `new` and `play` work offline
from the Game rules installed with the package. A Bot file records the version of its Game's rules it was written for
(`GAME_VERSION`), and every command warns when that, the installed rules and the platform's drift apart (drift.py)."""
import json
import os
import random
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated

import httpx
import typer
from typer.core import TyperGroup, TyperOption
from rich.console import Console, Group
from rich.pager import Pager
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .. import __version__
from .boards import board_text
from ..drift import bot_vs_installed, installed_vs_platform
from ..games import GAMES, Game, game_info
from ..docs import guide
from .local import Bot, BotFileError, load_bot, play_match, random_bot
from ..sdk import DEFAULT_URL, TOKEN_VAR, URL_VAR, ApiError, outcome
from ..sdk import run as sdk_run
from .starter import ignore_env, save_token, starter_bot, token_from_env_file
from .style import COMMAND, games_table, render_guide

_type_of = TyperOption.display_type_rich
# `--help` shows no <bool> next to an on/off flag such as --show: Typer's rich help prints every option's type.
TyperOption.display_type_rich = lambda self, ctx: None if self.is_flag else _type_of(self, ctx)

ORDER = ["new", "play", "run", "games", "game", "health"]  # as a developer uses them
WRITE, GAMES_PANEL, PLATFORM = "Write a Bot", "Games", "Platform"


class Commands(TyperGroup):
    """`botingame --help` lists the commands in ORDER, not in the order they are defined."""

    def list_commands(self, ctx) -> list[str]:
        return sorted(super().list_commands(ctx), key=ORDER.index)


app = typer.Typer(
    help="BotInGame: write a Bot, try it offline against the real Game rules, then play it on the platform.",
    no_args_is_help=True, add_completion=False, rich_markup_mode="rich", cls=Commands)


def fail(message: str) -> typer.Exit:
    """Print the error; returns the non-zero exit for the caller to raise."""
    typer.echo(f"Error: {message}", err=True)
    return typer.Exit(1)


def game_of(key: str) -> Game:
    if key not in GAMES:
        raise fail(f"unknown Game {key!r}. The Games are: {', '.join(GAMES)}")
    return GAMES[key]


def as_json(value) -> str:
    return json.dumps(value, indent=2)


def show_version(value: bool):
    if value:
        typer.echo(f"botingame {__version__}")
        raise typer.Exit()


@app.callback()
def main(version: Annotated[bool, typer.Option("--version", callback=show_version, is_eager=True,
                                               help="Print the package version and exit.")] = False):
    pass


Url = Annotated[str, typer.Option(envvar=URL_VAR, help="The Bot API's URL.")]
WEB_URL = "https://botingame.com"
WEB_URL_VAR = "BOTINGAME_WEB_URL"  # the environment variable overriding WEB_URL
WebUrl = Annotated[str, typer.Option(envvar=WEB_URL_VAR, help="The web app's URL (health check, Match links).")]


def check(url: str, timeout: float) -> tuple[str, str, str]:
    """GET <url>/healthz: (state, what it said, how long it took). state is up, down or slow (no answer in time, as
    when a free-tier service is waking up)."""
    try:
        r = httpx.get(url.rstrip("/") + "/healthz", timeout=timeout)
    except httpx.TimeoutException:
        return "slow", f"no answer in {timeout:.0f} s", "-"
    except httpx.HTTPError:
        return "down", "unreachable", "-"
    detail = str(r.status_code)
    if r.headers.get("content-type", "").startswith("application/json"):
        detail += ", " + ", ".join(f"{k} {v}" for k, v in r.json().items() if k != "status")
    return "up" if r.status_code == 200 else "down", detail, f"{r.elapsed.total_seconds():.1f} s"


def check_all(web_url: str, url: str, timeout: float) -> list[tuple[str, str, tuple[str, str, str]]]:
    """Both services, checked at the same time: [(name, url, check result)]."""
    services = [("Web app", web_url), ("Bot API", url)]
    with ThreadPoolExecutor() as pool:
        results = list(pool.map(lambda service: check(service[1], timeout), services))
    return [(name, base, result) for (name, base), result in zip(services, results)]


STATE = {"up": "[green]● up[/]", "down": "[red]● down[/]", "slow": "[yellow]● slow[/]"}


def health_header(web_url: str, url: str) -> None:
    """One line on top of a live command: is the platform up? A short timeout, so it never holds the command up."""
    parts = [f"{name} {STATE[state]} [dim]{took if state == 'up' else detail}[/]"
             for name, _, (state, detail, took) in check_all(web_url, url, timeout=5)]
    Console(highlight=False).print("  ·  ".join(parts) + "\n")
Offline = Annotated[bool, typer.Option(
    "--offline", help="Use the Game rules installed with this package, which may be older than the platform's.")]


def warn(warnings: list[str]) -> None:
    for warning in warnings:
        typer.echo(f"Warning: {warning}")


def installed_version(key: str) -> str | None:
    return GAMES[key].version if key in GAMES else None


def fetch(url: str, path: str) -> httpx.Response:
    """A public read of the Bot API (no token)."""
    try:
        return httpx.get(url.rstrip("/") + path, timeout=15)
    except httpx.HTTPError as e:
        raise fail(f"cannot reach {url} ({e}). Pass --offline to use the Game rules installed with this package")


def platform_version(url: str, key: str) -> str | None:
    """The platform's version of a Game, or None if the Bot API cannot tell (unreachable, or no such Game)."""
    try:
        r = httpx.get(f"{url.rstrip('/')}/v1/games/{key}", timeout=5)
    except httpx.HTTPError:
        return None
    return r.json()["version"] if r.status_code == 200 else None


def platform_games(url: str) -> list[dict]:
    r = fetch(url, "/v1/games")
    if r.status_code != 200:
        raise fail(f"{url} answered {r.status_code} for /v1/games")
    return r.json()


def on_terminal(menu: bool = False) -> bool:
    """Is someone at a terminal to answer questions (stdin), or also to drive a full-screen menu (stdout too)?"""
    return sys.stdin.isatty() and (not menu or sys.stdout.isatty())


def show_menu(rows: list[dict], load_page: Callable[[str], str] | None = None) -> str | None:
    """The inline Game menu (menu.py). With `load_page` (a Game's key -> its guide), browses: Enter shows the guide as
    `botingame game` does, and quitting it comes back to the list. Else picks a Game and returns its key (None if
    quit). questionary loads only here, so the other commands start fast."""
    from .menu import browse, pick_game
    if load_page is None:
        return pick_game(rows)
    browse(rows, lambda key: print_guide(load_page(key)))


def platform_game(url: str, key: str) -> dict:
    """A Game as the platform serves it, with its guide; raises LookupError (unknown Game) or ConnectionError, with
    what went wrong."""
    try:
        r = httpx.get(f"{url.rstrip('/')}/v1/games/{key}", timeout=15)
    except httpx.HTTPError as e:
        raise ConnectionError(f"cannot reach {url} ({e})") from e
    if r.status_code == 404:
        raise LookupError(key)
    if r.status_code != 200:
        raise ConnectionError(f"{url} answered {r.status_code} for /v1/games/{key}")
    return r.json()


@app.command(short_help="List the Games, and read their guides", rich_help_panel=GAMES_PANEL)
def games(url: Url = DEFAULT_URL, offline: Offline = False, web_url: WebUrl = WEB_URL,
          plain: Annotated[bool, typer.Option("--plain", help="Print the table and exit, even in a terminal.")]
          = False):
    """List the platform's Games: key (what --game takes), name, players and version. In a terminal, pick one
    to read its guide: ↑/↓ (or j/k) move, Enter or → opens the guide (in a pager when it is long: q there comes back
    to the list), q or Esc quits. Piped, or with --plain, it prints the table."""
    if not offline:
        health_header(web_url, url)
    infos = [game_info(g) for g in GAMES.values()] if offline else platform_games(url)
    if not offline:  # under the health line, before the list
        for g in infos:
            warn(installed_vs_platform(g["id"], g["version"], installed_version(g["id"])))
    if on_terminal(menu=True) and not plain:
        def page(key: str) -> str:
            if offline:
                return guide(GAMES[key])
            try:
                return platform_game(url, key)["guide"]
            except (LookupError, ConnectionError) as e:
                return f"# {key}\n\nCould not load this guide: {e}. Try `botingame game {key} --offline`."
        show_menu(infos, page)
    else:
        Console(highlight=False).print(games_table(infos))


def print_guide(markdown: str, use_pager: bool = True, console: Console | None = None,
                pager: Pager | None = None) -> None:
    """Show a Game guide. On a terminal: rendered (headings, tables, highlighted code), in a pager when it is taller
    than the terminal unless `use_pager` is off. Elsewhere (piped, in tests): the Markdown source as plain text.
    `pager` replaces the system pager (tests)."""
    console = console or Console()
    if not console.is_terminal:
        print(markdown, file=console.file)
        return
    rendered = render_guide(markdown)
    if use_pager and len(console.render_lines(rendered, pad=False)) > console.height:
        with console.pager(pager, styles=True):
            console.print(rendered)
    else:
        console.print(rendered)


@app.command(short_help="Show a Game's technical guide", rich_help_panel=GAMES_PANEL)
def game(key: Annotated[str, typer.Argument(help="The Game's key, as `botingame games` lists it.")],
         url: Url = DEFAULT_URL, offline: Offline = False, web_url: WebUrl = WEB_URL,
         no_pager: Annotated[bool, typer.Option("--no-pager", help="Print the guide straight, without a pager.")]
         = False):
    """Show a Game's technical guide: its exact rules, how a Bot plays it, the view and the move (with their JSON
    Schemas and examples), and code to start from; the illustrated rules are on the Game's rules page at
    botingame.com. On a terminal it opens in a pager when taller than the screen; piped, it prints the Markdown
    source."""
    if not offline:
        health_header(web_url, url)
    if offline:
        text = guide(game_of(key))
    else:
        try:
            info = platform_game(url, key)
        except LookupError:
            raise fail(f"unknown Game {key!r}. The Games are: {', '.join(g['id'] for g in platform_games(url))}")
        except ConnectionError as e:
            raise fail(f"{e}. Pass --offline to use the Game rules installed with this package")
        text = info["guide"]
    print_guide(text, use_pager=not no_pager)
    if not offline and (warnings := installed_vs_platform(key, info["version"], installed_version(key))):
        typer.echo("")
        warn(warnings)


BotPath = Annotated[str, typer.Argument(help="The Bot file: a Python file with choose_move(view, legal_moves).")]


def load(path: str) -> Bot:
    try:
        return load_bot(path)
    except BotFileError as e:
        raise fail(str(e))


class StopPlay(Exception):
    """`play --step`: the developer typed q (or Ctrl+C, or closed the input)."""


def step(console: Console, prompt: Text) -> None:
    """`play --step`'s pause: wait for Enter; q (or the end of the input) stops the run, as Ctrl+C does."""
    try:
        answer = console.input(Text.assemble(prompt, ("  Enter plays, q stops ", "dim")))
    except EOFError as e:
        raise StopPlay from e
    if answer.strip().lower() in ("q", "quit"):
        raise StopPlay


OUTCOME = {"win": "bold green", "loss": "bold red", "draw": "bold yellow"}


def tally_table(tally: dict[str, int]) -> Table:
    """The end of `play`: how many Matches, won, lost and drawn."""
    table = Table(box=None, padding=(0, 2, 0, 0), header_style="bold")
    table.add_column("Matches", justify="right")
    for column, word in (("Wins", "win"), ("Losses", "loss"), ("Draws", "draw")):
        table.add_column(column, justify="right", style=OUTCOME[word].removeprefix("bold "))
    table.add_row(str(sum(tally.values())), *(str(tally[word]) for word in ("win", "loss", "draw")))
    return table


@app.command(short_help="Play Matches offline, to test a Bot", rich_help_panel=WRITE)
def play(bot: BotPath,
         game: Annotated[str | None, typer.Option(help="The Game's key (default: the Bot file's GAME).")] = None,
         vs: Annotated[str, typer.Option(help="The opponent: `random`, or another Bot file.")] = "random",
         matches: Annotated[int, typer.Option(min=1, help="How many Matches, alternating seats.")] = 1,
         seed: Annotated[int | None, typer.Option(help="Replay the same Matches (default: a new random seed).")] = None,
         show: Annotated[bool, typer.Option("--show", help="Print the board after every move.")] = False,
         step_by_step: Annotated[bool, typer.Option(
             "--step", help="Pause before every move (and between Matches): Enter plays one move and shows the "
                            "board, q then Enter (or Ctrl+C) stops. Implies --show; needs a terminal.")] = False):
    """Play Matches offline, with the same Game rules as the platform, and print the wins, losses and draws."""
    if step_by_step and not on_terminal():
        raise fail("no terminal to step through the Match: --step waits for Enter before each move")
    show = show or step_by_step
    console = Console(highlight=False)
    mine = load(bot)
    key = game or mine.game
    if key is None:
        raise fail("which Game? Pass --game (see `botingame games`), or set GAME = \"<key>\" in the Bot file")
    g = game_of(key)
    warn(bot_vs_installed(key, g.version, mine.game_version))
    opponent = None if vs == "random" else load(vs)
    if seed is None:
        seed = random.SystemRandom().randrange(1_000_000)
    names = [Path(bot).name, vs if opponent is None else Path(vs).name]
    console.print(Text.assemble((g.name, "bold"), ": ", (names[0], "cyan"), " vs ", (names[1], "magenta"),
                                f", {matches} Match{'es' * (matches > 1)} ", (f"(--seed {seed})", "dim")))
    seeds = random.Random(seed)
    tally = {"win": 0, "loss": 0, "draw": 0}
    try:
        for i in range(matches):
            if step_by_step and i > 0:
                console.print()
                step(console, Text(f"Match {i + 1} of {matches}: press Enter", style="bold"))
            match_seed, bots_seed, random_seed = (seeds.randrange(2**31) for _ in range(3))
            random.seed(bots_seed)  # Bots that use the `random` module replay too
            other = opponent or random_bot(random.Random(random_seed))
            my_seat = i % 2
            bots = [mine, other] if my_seat == 0 else [other, mine]
            who = {my_seat: ("you", "cyan"), 1 - my_seat: (names[1].removesuffix(".py"), "magenta")}

            def before(index, seat):
                console.print()
                step(console, Text.assemble((f"Move {index + 1}", "bold"), ": seat ", str(seat), " (",
                                            who[seat], ") to play"))

            def shown(index, seat, move, state):
                console.print()
                console.print(Text.assemble((f"Move {index + 1}", "bold"), ": seat ", (str(seat), who[seat][1]),
                                            " plays ", (json.dumps(move), "bold")))
                console.print(Text(board_text(g.id, state)))

            result = play_match(g, bots, match_seed, shown if show else None, before if step_by_step else None)
            result_word = outcome(result.scores[my_seat])
            tally[result_word] += 1
            if show:
                console.print()
            console.print(Text.assemble((f"Match {i + 1}", "bold"), f" (you: seat {my_seat}): ",
                                        (result_word, OUTCOME[result_word]),
                                        f", {result.reason}, {result.moves} moves"))
    except (StopPlay, KeyboardInterrupt) as stop:  # --step: q, the end of the input or Ctrl+C; the tally counts
        if isinstance(stop, KeyboardInterrupt) and not step_by_step:
            raise
        console.print("\n[bold yellow]Stopped.[/]")
    console.print()
    console.print(tally_table(tally))


def ask(question: str, flag: str, **prompt) -> str:
    """Ask a question at the terminal; without one, fail with the flag that answers it instead of waiting."""
    if not on_terminal():
        raise fail(f"no terminal to ask {question!r}: pass {flag}")
    return typer.prompt(typer.style(question, bold=True), **prompt)


def ask_game() -> str:
    """The Game's key, picked from the menu."""
    if not on_terminal(menu=True):
        raise fail("no terminal to pick the Game from: pass --game <key> (the Games: "
                   f"{', '.join(GAMES)})")
    key = show_menu([game_info(g) for g in GAMES.values()])
    if key is None:
        raise fail("no Game picked; nothing written")
    return key


def summary(path: str, game: str, env: Path, token_saved: bool) -> Panel:
    """What `new` wrote, and the commands to run next: `play` to test locally, then `run`."""
    done, todo = ("✓ ", "bold green"), ("! ", "bold yellow")
    lines = [Text.assemble(done, "Wrote ", (path, "bold"), f", a random-move Bot for {game}"),
             Text.assemble(done, "Saved ", TOKEN_VAR, " in ", (str(env), "bold"), " (git-ignored)") if token_saved
             else Text.assemble(todo, "No token yet: add ", f"{TOKEN_VAR}=big_...", " to ", (str(env), "bold"),
                                " before `botingame run`"),
             Text.assemble(done, (str(env.parent / ".gitignore"), "bold"), " lists .env"),
             Text(""), Text("Next:", style="bold"),
             Text.assemble("  ", (f"botingame play {path}", COMMAND), "   test it offline against a random Bot"),
             Text.assemble("  ", (f"botingame run {path}", COMMAND), "    then play ranked Matches on the platform")]
    return Panel(Group(*lines), title="Bot ready", title_align="left", border_style="green", expand=False)


@app.command(short_help="Write a starter Bot and keep its token", rich_help_panel=WRITE)
def new(game: Annotated[str | None, typer.Option(help="The Game's key (asked if left out).")] = None,
        path: Annotated[str | None, typer.Option(help="Where to write the Bot file (default: <game>_bot.py).")] = None,
        token: Annotated[str | None, typer.Option(
            help="The Bot's token, from your Dashboard; saved to .env next to the Bot file. Empty: add it later.")]
        = None,
        url: Url = DEFAULT_URL,
        offline: Annotated[bool, typer.Option(
            "--offline", help="Link the Bot to the installed rules without checking the platform's version.")] = False):
    """Set up a Bot: write a starter Bot file, linked to its Game's version, and keep its token in a git-ignored .env
    file. Asks for what --game, --path and --token leave out: the Game from an arrow-key menu (↑/↓ or j/k, Enter
    picks, q quits). Without a terminal, pass all three."""
    key = game_of(game).id if game is not None else ask_game()
    if path is None:
        path = ask("Bot file", "--path <file.py>", default=f"{key}_bot.py")
    bot = Path(path)
    if bot.exists():
        raise fail(f"{path} already exists; pick another --path")
    if token is None:
        token = ask("Bot token (hidden; Enter to add it later)", "--token <token> (or --token '' to add it later)",
                    default="", hide_input=True, show_default=False)
    version = GAMES[key].version
    if not offline:
        if (platform := platform_version(url, key)) is None:
            typer.echo(f"Note: could not check the platform's {key} version at {url}; the Bot is linked to the "
                       f"installed rules, {key} {version}.")
        else:
            warn(installed_vs_platform(key, platform, version))
            version = platform
    bot.parent.mkdir(parents=True, exist_ok=True)
    bot.write_text(starter_bot(key, path, version))
    ignore_env(bot.parent / ".gitignore")
    env = bot.parent / ".env"
    if token.strip():
        save_token(env, token.strip())
    Console(highlight=False).print(summary(path, f"{GAMES[key].name} {version}", env, bool(token.strip())))


def points(x: float) -> str:
    """A Series score: 2, 1½, ½."""
    whole, half = int(x), x % 1 == 0.5
    return ("" if whole == 0 and half else str(whole)) + ("½" if half else "")


def _sides(m: dict) -> tuple[dict, dict]:
    """(the Bot's player, its opponent) in a Match view."""
    me = m["players"][m["your_seat"]]
    return me, next(p for p in m["players"] if p is not me)


def player_line(p: dict, mine: bool = False) -> str:
    """A player's name and Elo; then its seat for the Bot's own, else its creator."""
    parts = [f"[bold]{escape(p['name'])}[/]", f"Elo {round(p['rating'])}"]
    if mine:
        parts.append(f"seat {p['seat']}")
    elif p.get("creator"):
        parts.append(f"by {escape(p['creator'])}")
    return " · ".join(parts)


def matched_block(m: dict, web_url: str) -> str:
    """When the Bot has a Match: where to watch it, who it plays, its own Elo and seat, and the Series format."""
    me, opp = _sides(m)
    link = f"{web_url.rstrip('/')}/matches/{m['match_id']}"
    series = m["series"]
    return "\n".join([
        f"[bold]Match {series['match_number']} of a best-of-{series['best_of']}[/] in {m['arena']}",
        f"  Watch     [link={link}]{link}[/link]",
        f"  Opponent  {player_line(opp)}",
        f"  You       {player_line(me, mine=True)}"])


RESULT_STYLE = {"win": "green", "draw": "yellow", "loss": "red"}


def finished_lines(m: dict) -> list[str]:
    """The end of a Match: its result, reason and moves; then the Series so far, or its result and the Elo change."""
    me, opp = _sides(m)
    series = m["series"]
    word = outcome(m["result"][m["your_seat"]])
    lines = [f"Match {series['match_number']}: [{RESULT_STYLE.get(word, 'bold')}]{word}[/] ({m['reason']}), "
             f"{m['turn']} moves"]
    mine, theirs = series["score"][me["bot_id"]], series["score"][opp["bot_id"]]
    score = f"{points(mine)}–{points(theirs)}"
    if series["status"] != "finished":
        left = series["best_of"] - series["match_number"]
        lines.append(f"  Series {score}, at most {left} Match{'es' if left != 1 else ''} left")
        return lines
    verdict = "won" if mine > theirs else "lost" if mine < theirs else "drew"
    line = f"[bold]You {verdict} the Series {score}[/]"
    if change := (series.get("rating_change") or {}).get(me["bot_id"]):
        before, after = round(change["before"]), round(change["after"])
        line += f" · Elo {before} → [bold]{after}[/] ({after - before:+d})"
    return lines + [line]


class RunOutput:
    """`run`'s output: a spinner while queueing, then a block per Match as it starts and lines as it ends."""

    def __init__(self, web_url: str):
        self.console, self.web_url, self.waiting = Console(highlight=False), web_url, None

    def log(self, message: str) -> None:
        self.console.print(message, markup=False)

    def stop_waiting(self) -> None:
        if self.waiting is not None:
            self.waiting.stop()
            self.waiting = None

    def on_event(self, kind: str, m: dict) -> None:
        if kind == "queueing":
            waiting = f"Waiting for an opponent in {m['arena']}…"
            if self.console.is_terminal:
                self.waiting = self.console.status(waiting)
                self.waiting.start()
            else:
                self.log(waiting)
            return
        self.stop_waiting()
        if kind == "matched":
            self.console.print("\n" + matched_block(m, self.web_url))
        elif kind == "finished":
            for line in finished_lines(m):
                self.console.print(line)


@app.command(short_help="Play ranked Series on the platform", rich_help_panel=WRITE)
def run(bot: BotPath,
        token: Annotated[str | None, typer.Option(
            help="The Bot's token (default: BOTINGAME_TOKEN, else a .env file in this folder or the Bot file's).")]
        = None,
        arena: Annotated[str | None, typer.Option(help="The Arena to queue in (default: the Game's ranked one).")]
        = None,
        series: Annotated[int, typer.Option(min=0, help=(
            "How many Series to play; 0 plays until Ctrl+C. A Series is always played to its end, every Match of "
            "a best-of-X."))] = 1,
        url: Annotated[str, typer.Option(envvar=URL_VAR, help="The Bot API's URL.")] = DEFAULT_URL,
        min_move_s: Annotated[float, typer.Option(
            min=0, help="The least time a move takes, which keeps the Bot under the rate limit.")] = 0.5,
        web_url: WebUrl = WEB_URL):
    """Connect the Bot to the platform and play ranked Series: one by default. For each Match it shows where to
    watch it, the opponent, both Elos and the Series score; at the end of the Series, the Elo change."""
    health_header(web_url, url)
    token = (token or os.environ.get(TOKEN_VAR) or token_from_env_file(Path(".env"))
             or token_from_env_file(Path(bot).parent / ".env"))
    if not token:
        raise fail(f"no Bot token: pass --token, set {TOKEN_VAR}, or add {TOKEN_VAR}=big_... to .env in this folder")
    mine = load(bot)
    out = RunOutput(web_url)
    try:
        try:
            sdk_run(mine.choose_move, token, game=mine.game, game_version=mine.game_version, arena=arena,
                    series=series, base_url=url, min_move_s=min_move_s, log=out.log, on_event=out.on_event)
        finally:
            out.stop_waiting()
    except ApiError as e:
        raise fail(e.detail)
    except ValueError as e:
        raise fail(str(e))
    except ConnectionError as e:
        raise fail(f"cannot reach {url}: {e}")
    except KeyboardInterrupt:
        typer.echo("Stopped.")


@app.command(short_help="Check that the platform is up", rich_help_panel=PLATFORM)
def health(url: Url = DEFAULT_URL, web_url: WebUrl = WEB_URL):
    """Check that the platform's web app and Bot API are up; exits non-zero if either is down."""
    console = Console()
    table = Table(box=None, padding=(0, 2), header_style="bold")
    for column in ("Service", "Status", "Details", "Time", "URL"):
        table.add_column(column, no_wrap=True)
    with console.status("Checking (a sleeping service can take up to a minute to wake)..."):
        results = check_all(web_url, url, timeout=60)
    for name, base, (state, detail, took) in results:
        table.add_row(name, STATE[state], detail, took, f"[dim]{base}[/]")
    console.print(table)
    if any(state != "up" for _, _, (state, _, _) in results):
        raise typer.Exit(1)

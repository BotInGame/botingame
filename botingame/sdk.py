"""The Bot SDK: you write `choose_move(view, legal_moves)`, `run` does the rest over the `/v1` Bot API.

`run` authenticates with the Bot's token, resumes the Bot's active Match if it has one (after a crash, or the next
Match of a best-of-X Series), otherwise queues into the Arena, then long-polls for its turn and posts each move with
its turn number. It counts whole Series, and never stops inside one. Dropped connections and `5xx` are retried (a
repeated `(turn, move)` is idempotent on the server).
A `429` waits out its `Retry-After` (at least 1s) for as long as it lasts, because giving up would forfeit a Match the
Bot can still finish; after a long run of them, `run` says what usually causes it (another process on the same token).

Keeping under the rate limit (10 requests/s per token) is the Bot's job: `run` takes at least `min_move_s` per move,
so a fast `choose_move` never rushes a Match.
"""
import os
import time
from collections.abc import Callable
from typing import Any, Protocol

import httpx

from .drift import bot_vs_platform, installed_vs_platform
from .games import GAMES

DEFAULT_URL = "https://api.botingame.com"
TOKEN_VAR = "BOTINGAME_TOKEN"  # the environment variable holding the Bot's token
URL_VAR = "BOTINGAME_URL"  # the environment variable overriding DEFAULT_URL
POLL_S = 25  # how long each long-poll holds (the server allows up to 30)
RETRIES = 6  # tries after a dropped connection or a 5xx, backing off 1, 2, 4… seconds (at most 30)
LIMITED_HINT_AT = 10  # 429s in a row on one call before saying what usually causes them

ChooseMove = Callable[[Any, list], Any]


class Http(Protocol):
    """What the SDK needs of an HTTP client: httpx.Client, or a test app's TestClient."""

    def request(self, method: str, url: str, **kw) -> httpx.Response: ...


class ApiError(Exception):
    """The Bot API refused a request (a `4xx` other than `429`)."""

    def __init__(self, status: int, detail: str):
        super().__init__(f"{status}: {detail}")
        self.status, self.detail = status, detail


class Client:
    """The `/v1` Bot API with a token: every call retried on dropped connections and `5xx`, and paced on `429`."""

    def __init__(self, token: str, http: Http, sleep: Callable[[float], None] = time.sleep,
                 log: Callable[[str], None] = print):
        self.http, self.sleep, self.log = http, sleep, log
        self.headers = {"Authorization": f"Bearer {token}"}

    def call(self, method: str, path: str, body: Any = None) -> dict:
        failures = limited = 0
        while True:
            try:
                r = self.http.request(method, path, json=body, headers=self.headers)
            except httpx.TransportError as e:
                failures = self._back_off(failures, f"{type(e).__name__}: {e}")
                continue
            if r.status_code == 429:
                wait = _retry_after_s(r.headers.get("Retry-After"))
                limited += 1
                self.log(f"rate limited: waiting {wait:g}s")
                if limited == LIMITED_HINT_AT:
                    self.log(f"still rate limited after {limited} tries: is another process using this token? "
                             f"Each token shares one rate limit, so stop the other `botingame run`")
                self.sleep(wait)
                continue
            if r.status_code >= 500:
                failures = self._back_off(failures, f"server error {r.status_code}")
                continue
            if r.status_code >= 400:
                raise ApiError(r.status_code, _detail(r))
            return r.json()

    def _back_off(self, failures: int, why: str) -> int:
        if failures >= RETRIES:
            raise ConnectionError(f"giving up after {failures + 1} tries: {why}")
        wait = min(30, 2 ** failures)
        self.log(f"{why}; retrying in {wait}s")
        self.sleep(wait)
        return failures + 1


OnEvent = Callable[[str, dict], None]


def run(choose_move: ChooseMove, token: str | None = None, *, game: str | None = None,
        game_version: str | None = None, arena: str | None = None, series: int = 1, base_url: str | None = None,
        http: Http | None = None, min_move_s: float = 0.5,
        sleep: Callable[[float], None] = time.sleep, log: Callable[[str], None] = print,
        on_event: OnEvent | None = None) -> list[dict]:
    """Play `series` whole Series (0: until stopped) with `choose_move(view, legal_moves)`, which gets the Bot's view
    of the Game state and its legal moves, and returns one of them. Returns each finished Match as the Bot API shows it.

    A Series is always played to its end: `run` never stops between two Matches of a best-of-X Series, which would
    leave the Bot to time out in the rest. A Series already going on when `run` starts is resumed, and counts as the
    first.

    `token` defaults to `BOTINGAME_TOKEN`; `game`, if given, must be the token's Game; `game_version` is the version of
    its rules the Bot was written for, and a warning is logged when it, or the rules installed with this package,
    differ from the platform's. `arena` defaults to the Game's ranked Arena (`<game>-elo`); `base_url` to
    `BOTINGAME_URL`, else the platform. `http` replaces the HTTP client (tests pass a test app's client).

    `on_event(kind, match_view)` follows the Matches: `"queueing"` (with only `{"arena"}`) when the Bot starts
    waiting for an opponent, `"matched"` when it has a Match to play (new, resumed, or the next of its Series) and
    `"finished"` at the end of each one; the view carries `players` (with each one's `rating` and `creator`) and
    `series` (with its `rating_change` once the Series is over). Without it, `log` gets one line for each."""
    token = token or os.environ.get(TOKEN_VAR)
    if not token:
        raise ValueError(f"no Bot token: pass token= or set {TOKEN_VAR}")
    if http is None:
        http = httpx.Client(base_url=base_url or os.environ.get(URL_VAR) or DEFAULT_URL, timeout=POLL_S + 15)
    api = Client(token, http, sleep, log)
    me = api.call("GET", "/v1/bots/me")
    if game is not None and game != me["game"]:
        raise ValueError(f"this token is for a {me['game']} Bot, but the Bot file plays {game}")
    arena = arena or f"{me['game']}-elo"
    log(f"{me['name']} ({me['game']}) is online")
    platform = api.call("GET", f"/v1/games/{me['game']}")["version"]
    installed = GAMES[me["game"]].version if me["game"] in GAMES else None
    for warning in installed_vs_platform(me["game"], platform, installed) + bot_vs_platform(me["game"], platform,
                                                                                            game_version):
        log(f"Warning: {warning}")
    on_event = on_event or _logged(log)
    finished: list[dict] = []
    done = 0  # whole Series played
    while series == 0 or done < series:
        current = api.call("GET", "/v1/bots/me/match")  # a resumed Match, or the next one of the Series
        if current.get("status") == "none":
            on_event("queueing", {"arena": arena})
            if (match_id := _queue(api, arena)) is None:
                continue  # already queued or paired elsewhere: look for the Match again
            current = api.call("GET", f"/v1/matches/{match_id}")
        on_event("matched", current)
        m = _play(api, current["match_id"], choose_move, min_move_s)
        on_event("finished", m)
        finished.append(m)
        done += m["series"]["status"] != "active"
    return finished


def _logged(log: Callable[[str], None]) -> OnEvent:
    """The plain `on_event`: one `log` line per event."""
    def on_event(kind: str, m: dict) -> None:
        if kind == "queueing":
            log(f"queueing in {m['arena']}")
        elif kind == "matched":
            log(f"playing Match {m['match_id']}")
        elif kind == "finished":
            log(f"Match {m['match_id']}: {outcome(m['result'][m['your_seat']])} ({m['reason']})")
    return on_event


def outcome(score: float | None) -> str:
    """A seat's score in a finished Match, in words."""
    return {1: "win", 0.5: "draw", 0: "loss"}.get(score, "no result")


def _queue(api: Client, arena: str) -> str | None:
    """Queue into `arena` (a long-poll: the Bot stays queued only while polling) until paired. None on a `409`: the
    Bot is in a Match already (just paired, say), or an earlier run's queue poll is still open."""
    try:
        while (q := api.call("POST", f"/v1/arenas/{arena}/queue?wait={POLL_S}"))["status"] != "matched":
            pass
    except ApiError as e:
        if e.status != 409:
            raise
        api.log(f"cannot queue yet: {e.detail}")
        api.sleep(1)
        return None
    return q["match_id"]


def _play(api: Client, match_id: str, choose_move: ChooseMove, min_move_s: float) -> dict:
    """Play the Match to its end; returns its final view."""
    while True:
        m = api.call("GET", f"/v1/matches/{match_id}?wait={POLL_S}")  # returns on my turn or at the end
        if m["status"] == "finished":
            return m
        if not m.get("your_turn"):
            continue
        started = time.monotonic()
        move = choose_move(m["state"], m["legal_moves"])
        if (left := min_move_s - (time.monotonic() - started)) > 0:
            api.sleep(left)
        try:
            api.call("POST", f"/v1/matches/{match_id}/moves", {"turn": m["turn"], "move": move})
        except ApiError as e:
            if e.status not in (409, 422):
                raise
            # 409: the Match moved on (e.g. a timeout); 422: an illegal move. Either way, look again.
            api.log(f"turn {m['turn']}: move {move!r} refused: {e.detail}")


def _retry_after_s(header: str | None) -> float:
    try:
        return max(1.0, float(header))  # at least 1s, so a bad header can't make a tight loop
    except (TypeError, ValueError):
        return 1.0


def _detail(r: httpx.Response) -> str:
    try:
        return str(r.json().get("detail", r.text))
    except ValueError:
        return r.text

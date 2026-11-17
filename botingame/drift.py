"""Game version drift: the platform's rules for a Game, the rules installed with this package, and the version a Bot
was written for (its `GAME_VERSION`) should all be the same. Each check returns the warnings to show, if any."""
from importlib.metadata import version

UPGRADE = "`uv tool upgrade botingame` or `pip install -U botingame`"


def _key(v: str) -> tuple:
    return tuple(int(p) if p.isdigit() else p for p in v.split("."))


def _older(a: str, b: str) -> bool:
    try:
        return _key(a) < _key(b)
    except TypeError:
        return False


def installed_vs_platform(game: str, platform: str, installed: str | None) -> list[str]:
    """The installed rules against the platform's."""
    package = version("botingame")
    if installed is None:
        return [f"the platform runs {game} {platform}, but your botingame {package} does not have this Game: "
                f"update it ({UPGRADE}) to play it offline."]
    if installed == platform:
        return []
    if _older(installed, platform):
        return [f"the platform runs {game} {platform}, but your botingame {package} has {game} {installed}: "
                f"update it ({UPGRADE}). Until then, offline `play` runs older rules and your Bot may not play well "
                f"on the platform."]
    return [f"your botingame {package} has {game} {installed}, newer than the platform's {platform}: offline `play` "
            f"runs other rules than the platform, and your Bot may not play well there."]


def bot_vs_platform(game: str, platform: str, bot: str | None) -> list[str]:
    """The version the Bot was written for against the platform's."""
    if bot is None or bot == platform:
        return []
    return [f"your Bot was written for {game} {bot}, but the platform runs {game} {platform}: it may not play well. "
            f"Check the rules with `botingame game {game}`, update the Bot, then set GAME_VERSION = \"{platform}\"."]


def bot_vs_installed(game: str, installed: str, bot: str | None) -> list[str]:
    """The version the Bot was written for against the installed rules (offline `play`)."""
    if bot is None or bot == installed:
        return []
    if _older(installed, bot):
        return [f"your Bot was written for {game} {bot}, but your botingame {version('botingame')} has {game} "
                f"{installed}: update it ({UPGRADE}) so `play` runs the rules your Bot expects."]
    return [f"your Bot was written for {game} {bot}, but these are the {game} {installed} rules: it may not play "
            f"well. Check the rules with `botingame game {game} --offline`, update the Bot, then set "
            f"GAME_VERSION = \"{installed}\"."]

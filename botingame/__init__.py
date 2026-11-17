"""BotInGame: the Game rules the platform runs, the Bot SDK (`run`) and the `botingame` CLI."""
from importlib.metadata import version

from .sdk import ApiError, run

__version__ = version("botingame")

__all__ = ["ApiError", "__version__", "run"]

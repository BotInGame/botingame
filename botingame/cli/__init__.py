"""The `botingame` command: `commands.py` defines it; the rest serves its commands (`local` runs offline Matches for
`play`, `boards` draws them for `--show`, `starter` writes the Bot for `new`, `menu` is the Game menu, `style` the
look). Only re-exports."""
from .commands import app

__all__ = ["app"]

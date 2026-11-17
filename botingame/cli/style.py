"""How the CLI shows things with `rich`, so the commands look the same."""
from rich.markdown import Markdown
from rich.table import Table

KEY = "bold cyan"  # a Game's key, as --game takes it
COMMAND = "bold green"  # a command to type


def render_guide(markdown: str) -> Markdown:
    """A Game guide rendered for a terminal: headings, tables and highlighted code."""
    return Markdown(markdown, code_theme="monokai")


def games_table(games: list[dict]) -> Table:
    """The Games (as the Bot API lists them): key, name, players and version. The rules are on each Game's page."""
    table = Table(box=None, padding=(0, 2, 0, 0), header_style="bold")
    table.add_column("Key", style=KEY, no_wrap=True)
    table.add_column("Name", style="bold", no_wrap=True)
    table.add_column("Players", justify="right", no_wrap=True)
    table.add_column("Version", no_wrap=True)
    for g in games:
        table.add_row(g["id"], g["name"], str(g["players"]), g["version"])
    return table


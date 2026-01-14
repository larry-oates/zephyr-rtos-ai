import logging
from typing import Annotated

import typer
from typer import Typer

from zephyr_rtos_ai import __version__

from ._types import CmdState
from .kconfig._cli import kconfig_app

cli_app = Typer(name=f"Zephyr RTOS Client [{__version__}]")
cli_app.add_typer(kconfig_app, name="kconfig", help="Commands related to KConfig graph building and analysis")

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


@cli_app.callback()
def main(
    ctx: typer.Context,
    loglevel: Annotated[
        str,
        typer.Option(
            "--loglevel",
            "-l",
            help="Set the logging level (debug, info, warning, error, critical)",
        ),
    ] = "warning",
) -> None:
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("zephyr_rtos_ai").setLevel(LOG_LEVELS.get(loglevel, logging.WARNING))

    ctx.ensure_object(CmdState)

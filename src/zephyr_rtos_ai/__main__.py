import logging
from typing import Annotated

import typer
from typer import Typer

from zephyr_rtos_ai import __version__

from ._types import CmdState

cli_app = Typer(name=f"Zephyr RTOS Client [{__version__}]")

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

import os
from pathlib import Path
from typing import Final

from xdg_base_dirs import xdg_cache_home, xdg_data_home

_ZRA_DATA_HOME_ENV_VAR: Final[str] = "ZRA_DATA_HOME"


def _get_data_home() -> Path:
    env_zra_data = os.getenv(_ZRA_DATA_HOME_ENV_VAR, None)
    if env_zra_data:
        return Path(env_zra_data).expanduser().resolve()
    return xdg_data_home()


def _get_cache_home() -> Path:
    env_zra_data = os.getenv(_ZRA_DATA_HOME_ENV_VAR, None)
    if env_zra_data:
        return Path(env_zra_data).joinpath("cache").expanduser().resolve()
    return xdg_cache_home()


def _zra_directory(root: Path) -> Path:
    directory = root / "zra"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


def data_directory() -> Path:
    """Return (possibly creating) the application data directory."""
    return _zra_directory(_get_data_home())


def cache_directory() -> Path:
    return _zra_directory(_get_cache_home())

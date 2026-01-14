from .kconfig._types import KConfigCmdState


class CmdState:
    def __init__(self) -> None:
        self._kconfig: KConfigCmdState | None = None

    @property
    def kconfig(self) -> KConfigCmdState:
        if self._kconfig is None:
            raise ValueError("KConfigCmdState has not been set")
        return self._kconfig

    @kconfig.setter
    def kconfig(self, value: KConfigCmdState) -> None:
        self._kconfig = value

from ._models import KConfigDoc


class KConfigCmdState:
    def __init__(self) -> None:
        self._doc: KConfigDoc | None = None

    @property
    def doc(self) -> KConfigDoc:
        if self._doc is None:
            raise ValueError("KConfigDoc has not been set")
        return self._doc

    @doc.setter
    def doc(self, value: KConfigDoc) -> None:
        self._doc = value

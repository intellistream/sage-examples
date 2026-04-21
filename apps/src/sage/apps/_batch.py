from __future__ import annotations

from typing import Any

from sage.foundation import BatchFunction


class ListBatchSource(BatchFunction):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._batch_items: list[Any] | None = None
        self._batch_index = 0

    def load_items(self) -> list[Any]:
        raise NotImplementedError

    def execute(self) -> Any | None:
        if self._batch_items is None:
            self._batch_items = list(self.load_items())
            self._batch_index = 0

        if self._batch_index >= len(self._batch_items):
            return None

        item = self._batch_items[self._batch_index]
        self._batch_index += 1
        return item

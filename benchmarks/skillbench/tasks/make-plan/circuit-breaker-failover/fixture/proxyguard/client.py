from dataclasses import dataclass
from typing import Callable

class EndpointCallError(RuntimeError):
    pass

@dataclass(frozen=True)
class UpstreamResponse:
    endpoint: str
    payload: str

class UpstreamClient:
    def __init__(self, primary: Callable[[str], str]) -> None:
        self._primary = primary
    def call(self, key: str) -> UpstreamResponse:
        return UpstreamResponse('primary', self._primary(key))

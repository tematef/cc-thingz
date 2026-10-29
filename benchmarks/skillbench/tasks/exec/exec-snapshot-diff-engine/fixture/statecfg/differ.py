from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ChangeEntry:
    path: str
    kind: str  # 'added' | 'removed' | 'modified'
    old_value: Any = None
    new_value: Any = None

def diff_snapshots(before: dict[str, Any], after: dict[str, Any]) -> list[ChangeEntry]:
    out: list[ChangeEntry] = []
    for k in sorted(set(before) | set(after)):
        if k not in before:
            out.append(ChangeEntry(k, 'added', None, after[k]))
        elif k not in after:
            out.append(ChangeEntry(k, 'removed', before[k], None))
        elif before[k] != after[k]:
            out.append(ChangeEntry(k, 'modified', before[k], after[k]))
    return out

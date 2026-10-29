from dataclasses import dataclass

@dataclass
class FlagRule:
    flag_key: str
    enabled: bool = True
    rollout_pct: int = 100
    min_samples: int = 10
    max_error_rate: float = 0.2

class FlagController:
    def __init__(self) -> None:
        self._rules: dict[str, FlagRule] = {}
    def configure(self, rule: FlagRule) -> None:
        self._rules[rule.flag_key] = rule
    def evaluate(self, flag_key: str, subject_id: str) -> bool:
        rule = self._rules.get(flag_key)
        return bool(rule and rule.enabled and rule.rollout_pct > 0)

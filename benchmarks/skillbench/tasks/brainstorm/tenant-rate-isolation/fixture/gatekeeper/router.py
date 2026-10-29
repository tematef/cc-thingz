from dataclasses import dataclass

@dataclass
class TenantPolicy:
    tenant_id: str
    rpm_limit: int

@dataclass
class DispatchOutcome:
    accepted: bool
    reason: str

class RequestRouter:
    def __init__(self, max_inflight: int = 8) -> None:
        self.max_inflight = max_inflight
        self.inflight = 0
        self._policies: dict[str, TenantPolicy] = {}
        self._counts: dict[str, int] = {}
    def register(self, policy: TenantPolicy) -> None:
        self._policies[policy.tenant_id] = policy
        self._counts.setdefault(policy.tenant_id, 0)
    def acquire(self, tenant_id: str) -> DispatchOutcome:
        policy = self._policies[tenant_id]
        if self.inflight >= self.max_inflight:
            return DispatchOutcome(False, 'pool_saturated')
        if self._counts[tenant_id] >= policy.rpm_limit:
            return DispatchOutcome(False, 'rpm_exceeded')
        self.inflight += 1
        self._counts[tenant_id] += 1
        return DispatchOutcome(True, 'ok')
    def release(self, tenant_id: str) -> None:
        if self.inflight > 0:
            self.inflight -= 1

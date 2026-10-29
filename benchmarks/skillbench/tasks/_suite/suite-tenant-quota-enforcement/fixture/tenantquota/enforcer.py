from dataclasses import dataclass

@dataclass
class ProjectQuota:
    project_id: str
    org_id: str
    limit: int
    used: int = 0

class QuotaEnforcer:
    def __init__(self) -> None:
        self._projects: dict[str, ProjectQuota] = {}
        self._org_limits: dict[str, int] = {}
    def set_org_limit(self, org_id: str, limit: int) -> None:
        self._org_limits[org_id] = limit
    def register_project(self, project_id: str, org_id: str, limit: int) -> None:
        self._projects[project_id] = ProjectQuota(project_id, org_id, limit)
    def acquire(self, project_id: str, units: int = 1) -> bool:
        proj = self._projects[project_id]
        if proj.used + units > proj.limit:
            return False
        proj.used += units
        return True

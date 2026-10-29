from dataclasses import dataclass

@dataclass
class LegacyProfile:
    user_id: str
    full_name: str
    raw_address: str

class UserProfileStore:
    def __init__(self) -> None:
        self._rows: dict[str, LegacyProfile] = {}
    def put_v1(self, profile: LegacyProfile) -> None:
        self._rows[profile.user_id] = profile
    def get_v1(self, user_id: str) -> LegacyProfile | None:
        return self._rows.get(user_id)

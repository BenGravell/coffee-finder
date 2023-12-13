import dataclasses

import geo


@dataclasses.dataclass
class Options:
    amenity: str = "cafe"
    physical_address: geo.PhysicalAddress = dataclasses.field(
        default_factory=lambda: geo.PhysicalAddress(
            street="1912 Pike Place",
            city="Seattle",
            state="WA",
        )
    )
    radius_km: float = 1.0
    deny_list: list[str] = dataclasses.field(default_factory=lambda: ["Starbucks", "Dunkin"])
    travel_mode: str = "walking"
    max_results: int = 200
    attempt_reverse_geocoding: bool = False

    @property
    def radius(self) -> int:
        return int(self.radius_km * 1000)

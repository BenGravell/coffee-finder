import dataclasses

import geo


@dataclasses.dataclass
class Options:
    amenity: str
    physical_address: geo.PhysicalAddress
    radius_km: float
    deny_list: list[str]
    travel_mode: str
    max_results: int
    attempt_reverse_geocoding: bool

    @property
    def radius(self) -> int:
        return int(self.radius_km * 1000)

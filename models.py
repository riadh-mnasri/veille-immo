from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Listing:
    id: str                          # source:annonce_id (unique)
    source: str                      # "pap" | "seloger" | "leboncoin" | "bienici"
    url: str
    title: str
    price: int
    surface: Optional[float] = None
    chambres: Optional[int] = None
    commune: str = ""
    code_postal: str = ""
    description: str = ""
    photos: list[str] = field(default_factory=list)
    score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def prix_m2(self) -> Optional[float]:
        if self.surface and self.surface > 0:
            return round(self.price / self.surface, 0)
        return None

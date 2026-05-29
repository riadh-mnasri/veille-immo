from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Session

from models import Listing

DB_PATH = Path(__file__).parent / "listings.db"


class Base(DeclarativeBase):
    pass


class ListingRow(Base):
    __tablename__ = "listings"

    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String)
    price = Column(Integer)
    surface = Column(Float)
    chambres = Column(Integer)
    commune = Column(String)
    code_postal = Column(String)
    description = Column(Text)
    photos = Column(Text)  # JSON list
    score = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)


class Database:
    def __init__(self):
        self.engine = create_engine(f"sqlite:///{DB_PATH}")
        Base.metadata.create_all(self.engine)

    def is_known(self, listing_id: str) -> bool:
        with Session(self.engine) as session:
            return session.get(ListingRow, listing_id) is not None

    def save(self, listing: Listing) -> None:
        with Session(self.engine) as session:
            row = ListingRow(
                id=listing.id,
                source=listing.source,
                url=listing.url,
                title=listing.title,
                price=listing.price,
                surface=listing.surface,
                chambres=listing.chambres,
                commune=listing.commune,
                code_postal=listing.code_postal,
                description=listing.description[:2000],
                photos=json.dumps(listing.photos[:5]),
                score=listing.score,
                created_at=listing.created_at,
            )
            session.merge(row)
            session.commit()

    def all_listings(self) -> list[ListingRow]:
        with Session(self.engine) as session:
            return session.query(ListingRow).order_by(ListingRow.score.desc()).all()

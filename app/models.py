from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    watchlist = relationship("Watchlist", back_populates="owner", cascade="all, delete-orphan")


class Watchlist(Base):
    __tablename__ = "watchlist"

    id         = Column(Integer, primary_key=True, index=True)
    symbol     = Column(String, index=True)   # e.g. "AAPL" or "bitcoin"
    name       = Column(String)               # e.g. "Apple Inc." or "Bitcoin"
    asset_type = Column(String)               # "stock" or "crypto"
    user_id    = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="watchlist")

    __table_args__ = (
        UniqueConstraint("user_id", "symbol", "asset_type", name="uq_user_symbol_type"),
    )

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    password: str


class MarketItem(BaseModel):
    name: str
    symbol: str
    price: float
    change: float
    asset_type: str          # "stock" | "crypto"
    source: str              # "live" | "cache" | "fallback"


class HistoryPoint(BaseModel):
    date: str
    price: float


class WatchlistItemCreate(BaseModel):
    symbol: str
    name: str
    asset_type: str          # "stock" | "crypto"
    user_id: int


class WatchlistItemOut(BaseModel):
    id: int
    symbol: str
    name: str
    asset_type: str

    class Config:
        from_attributes = True

"""MarketFlow Live — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import inspect as sa_inspect, text as sa_text

from app.database import engine, Base
from app.routers import auth, market, search, watchlist, compare, news, ai


def _migrate_missing_columns():
    inspector = sa_inspect(engine)
    existing_tables = inspector.get_table_names()

    for table_name, table_obj in Base.metadata.tables.items():
        if table_name not in existing_tables:
            continue

        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}

        for column in table_obj.columns:
            if column.name not in existing_cols:
                col_type = column.type.compile(dialect=engine.dialect)
                stmt = f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {col_type}'
                print(f"[migrate] Adding missing column: {table_name}.{column.name}")
                with engine.connect() as conn:
                    conn.execute(sa_text(stmt))
                    conn.commit()


try:
    _migrate_missing_columns()
except Exception as e:
    print(f"[migrate] Column migration failed: {e}")
    print("[migrate] If saves still fail, delete marketflow.db and restart.")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MarketFlow Live API",
    description="Backend for the MarketFlow Live financial dashboard.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(market.router)
app.include_router(search.router)
app.include_router(watchlist.router)
app.include_router(compare.router)
app.include_router(news.router)
app.include_router(ai.router)


from app.services.market_data import get_stock_data, get_crypto_data_batch
from app.routers.market import DEFAULT_STOCKS, DEFAULT_CRYPTOS
from concurrent.futures import ThreadPoolExecutor
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.security import get_password_hash, verify_password


@app.get("/api/market-data", tags=["legacy"])
def legacy_market_data():
    """Legacy endpoint."""
    with ThreadPoolExecutor(max_workers=6) as executor:
        stocks = list(executor.map(get_stock_data, DEFAULT_STOCKS))
    cryptos = get_crypto_data_batch(DEFAULT_CRYPTOS)
    return {
        "stocks": stocks,
        "crypto": cryptos,
    }


@app.post("/api/register", response_model=schemas.UserOut, tags=["legacy"])
def legacy_register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Legacy endpoint."""
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/login", tags=["legacy"])
def legacy_login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """Legacy endpoint."""
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    return {"status": "success", "user_id": db_user.id, "email": db_user.email}


@app.get("/", tags=["health"])
def health_check():
    return {"status": "online", "message": "MarketFlow Live API v2.0"}

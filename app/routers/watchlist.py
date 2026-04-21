from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("/{user_id}", response_model=list[schemas.WatchlistItemOut])
def get_watchlist(user_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Watchlist)
        .filter(models.Watchlist.user_id == user_id)
        .all()
    )


@router.post("", response_model=schemas.WatchlistItemOut, status_code=201)
def add_to_watchlist(item: schemas.WatchlistItemCreate, db: Session = Depends(get_db)):
    print(f"[watchlist] Save request: symbol={item.symbol!r}, "
          f"name={item.name!r}, type={item.asset_type!r}, user_id={item.user_id}")

    user = db.query(models.User).filter(models.User.id == item.user_id).first()
    if not user:
        print(f"[watchlist] FAIL — user_id {item.user_id} not found in database")
        raise HTTPException(status_code=404, detail=f"User {item.user_id} not found")

    existing = (
        db.query(models.Watchlist)
        .filter(
            models.Watchlist.user_id == item.user_id,
            models.Watchlist.symbol == item.symbol,
            models.Watchlist.asset_type == item.asset_type,
        )
        .first()
    )
    if existing:
        print(f"[watchlist] DUPLICATE — {item.symbol} already in watchlist for user {item.user_id}")
        raise HTTPException(status_code=409, detail="Asset already in watchlist")

    new_item = models.Watchlist(
        symbol=item.symbol,
        name=item.name,
        asset_type=item.asset_type,
        user_id=item.user_id,
    )
    db.add(new_item)
    try:
        db.commit()
        db.refresh(new_item)
        print(f"[watchlist] OK — saved {item.symbol} (id={new_item.id})")
    except IntegrityError:
        db.rollback()
        print(f"[watchlist] IntegrityError — {item.symbol} duplicate caught by DB constraint")
        raise HTTPException(status_code=409, detail="Asset already in watchlist")
    except Exception as e:
        db.rollback()
        print(f"[watchlist] ERROR — unexpected database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return new_item


@router.delete("/{item_id}", status_code=200)
def remove_from_watchlist(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Watchlist).filter(models.Watchlist.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    db.delete(item)
    db.commit()
    return {"status": "removed", "item_id": item_id}

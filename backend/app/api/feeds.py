from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.feed import FeedSource
from app.services.feed_service import feed_service
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class FeedCreate(BaseModel):
    name: str
    url: str
    source_type: str = "RSS"
    description: Optional[str] = None
    fetch_interval_minutes: int = 60

class FeedResponse(FeedCreate):
    id: int
    is_active: bool
    last_fetched_at: Optional[datetime]
    total_items_found: int
    last_status: str
    last_error: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True # pydantic v2
        orm_mode = True # pydantic v1 fallback

@router.get("/", response_model=List[FeedResponse])
def list_feeds(db: Session = Depends(get_db)):
    return db.query(FeedSource).all()

@router.post("/", response_model=FeedResponse)
def create_feed(feed: FeedCreate, db: Session = Depends(get_db)):
    db_feed = FeedSource(
        name=feed.name,
        url=feed.url,
        source_type=feed.source_type,
        description=feed.description,
        fetch_interval_minutes=feed.fetch_interval_minutes
    )
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return db_feed

@router.put("/{feed_id}/toggle")
def toggle_feed(feed_id: int, db: Session = Depends(get_db)):
    feed = db.query(FeedSource).filter(FeedSource.id == feed_id).first()
    if not feed: raise HTTPException(404, "Not found")
    feed.is_active = not feed.is_active
    db.commit()
    return {"status": "ok", "is_active": feed.is_active}

@router.post("/{feed_id}/fetch_now")
async def fetch_feed_now(feed_id: int):
    # Fire and forget or await? Await for manual trigger feedback
    count = await feed_service.fetch_feed(feed_id)
    return {"status": "ok", "new_items": count}

@router.delete("/{feed_id}")
def delete_feed(feed_id: int, db: Session = Depends(get_db)):
    db.query(FeedSource).filter(FeedSource.id == feed_id).delete()
    db.commit()
    return {"status": "ok"}

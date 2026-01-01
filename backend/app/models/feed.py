from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, func
from app.models.pipeline import Base
import enum

class FeedType(str, enum.Enum):
    RSS = "RSS"
    CSV = "CSV"
    JSON = "JSON"
    TEXT = "TEXT" # Line by line

class FeedSource(Base):
    __tablename__ = "feed_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    url = Column(String, nullable=False)
    source_type = Column(String, default=FeedType.RSS) # FeedType Enum
    
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Scheduling
    fetch_interval_minutes = Column(Integer, default=60)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    
    # Stats
    total_items_found = Column(Integer, default=0)
    last_status = Column(String, default="pending") # success, error, pending
    last_error = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

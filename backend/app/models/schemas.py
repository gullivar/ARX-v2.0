from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PipelineStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    BLOCKED = "BLOCKED"
    QUEUED = "QUEUED"
    CRAWLING = "CRAWLING"
    CRAWLED_SUCCESS = "CRAWLED_SUCCESS"
    CRAWLED_FAIL = "CRAWLED_FAIL"
    PROCESSING = "PROCESSING"
    ANALYZING = "ANALYZING"
    ANALYSIS_SUCCESS = "ANALYSIS_SUCCESS"
    ANALYSIS_FAIL = "ANALYSIS_FAIL"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class PipelineItemBase(BaseModel):
    fqdn: str
    source: Optional[str] = "manual"
    priority: int = 3

class PipelineItemCreate(PipelineItemBase):
    pass

class CrawlResultRead(BaseModel):
    url: Optional[str]
    http_status: Optional[int]
    title: Optional[str]
    crawled_at: Optional[datetime]
    class Config:
        from_attributes = True

class AnalysisResultRead(BaseModel):
    category_main: Optional[str]
    is_malicious: Optional[bool]
    confidence_score: Optional[float]
    summary: Optional[str]
    class Config:
        from_attributes = True

class PipelineItemResponse(PipelineItemBase):
    id: int
    status: PipelineStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    crawl_result: Optional[CrawlResultRead] = None
    analysis_result: Optional[AnalysisResultRead] = None
    
    class Config:
        from_attributes = True

class DomainFilterCreate(BaseModel):
    pattern: str
    type: str # WHITELIST, BLACKLIST
    description: Optional[str] = None

class DomainFilterResponse(DomainFilterCreate):
    id: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class PipelineLogResponse(BaseModel):
    id: int
    item_id: Optional[int]
    stage: str
    level: str
    message: str
    timestamp: datetime
    class Config:
        from_attributes = True

class PipelineStats(BaseModel):
    total: int
    by_status: dict[str, int]
    recent_items: List[PipelineItemResponse] = []
    recent_logs: List[PipelineLogResponse] = []

class ComponentStatus(BaseModel):
    name: str # e.g. "Crawler", "LLM", "VectorDB"
    status: str # "operational", "degraded", "down", "paused"
    details: Optional[str] = None
    last_check: datetime

class SystemHealth(BaseModel):
    status: str # "healthy", "degraded", "critical"
    components: List[ComponentStatus]

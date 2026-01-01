from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.pipeline import PipelineItem, AnalysisResult, CrawlResult, PipelineStatus, PipelineLog
from app.services.vector_service import vector_service

import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Schemas ---

class KBItemResponse(BaseModel):
    id: int
    fqdn: str
    category: str
    is_malicious: bool
    confidence: float
    summary: Optional[str]
    crawled_at: Optional[datetime]
    analyzed_at: Optional[datetime]
    vector_status: str = "Indexed" # Indexed / Missing

class KBStats(BaseModel):
    total_indexed: int
    categories: dict[str, int]
    malicious_count: int

class KBUpdateRequest(BaseModel):
    category: Optional[str] = None
    is_malicious: Optional[bool] = None
    summary: Optional[str] = None

# --- Endpoints ---

@router.get("/stats", response_model=KBStats)
def get_kb_stats(db: Session = Depends(get_db)):
    """
    Get generic stats about the Knowledge Base (Completed Items).
    """
    query = db.query(PipelineItem).join(AnalysisResult).filter(PipelineItem.status == PipelineStatus.COMPLETED)
    
    total = query.count()
    
    # Malicious count
    malicious = query.filter(AnalysisResult.is_malicious == True).count()
    
    # Categories breakdown
    from sqlalchemy import func
    cats = db.query(AnalysisResult.category_main, func.count(AnalysisResult.category_main))\
             .join(PipelineItem)\
             .filter(PipelineItem.status == PipelineStatus.COMPLETED)\
             .group_by(AnalysisResult.category_main).all()
    
    return {
        "total_indexed": total,
        "categories": {c: count for c, count in cats if c},
        "malicious_count": malicious
    }

@router.get("/items", response_model=dict)
def get_kb_items(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_malicious: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List KB items (Source: SQL AnalysisResults where status=COMPLETED).
    """
    query = db.query(PipelineItem, AnalysisResult).join(AnalysisResult).filter(PipelineItem.status == PipelineStatus.COMPLETED)
    
    if search:
        query = query.filter(PipelineItem.fqdn.ilike(f"%{search}%"))
    
    if category and category != "All":
        query = query.filter(AnalysisResult.category_main == category)
        
    if is_malicious is not None:
        query = query.filter(AnalysisResult.is_malicious == is_malicious)
        
    total = query.count()
    
    items = query.order_by(AnalysisResult.analyzed_at.desc())\
                 .offset((page - 1) * limit)\
                 .limit(limit).all()
                 
    results = []
    for item, analysis in items:
        results.append({
            "id": item.id,
            "fqdn": item.fqdn,
            "category": analysis.category_main,
            "is_malicious": analysis.is_malicious,
            "confidence": analysis.confidence_score,
            "summary": analysis.summary,
            "crawled_at": item.updated_at, # Approximate
            "analyzed_at": analysis.analyzed_at,
            "vector_status": "Indexed" # Assumed for now
        })
        
    return {
        "data": results,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.patch("/items/{id}")
def update_kb_item(id: int, req: KBUpdateRequest, db: Session = Depends(get_db)):
    """
    Update Metadata AND Re-Index Vector.
    """
    item = db.query(PipelineItem).filter(PipelineItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    analysis = db.query(AnalysisResult).filter(AnalysisResult.item_id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    # 1. Update SQL
    if req.category:
        analysis.category_main = req.category
    if req.is_malicious is not None:
        analysis.is_malicious = req.is_malicious
    if req.summary:
        analysis.summary = req.summary
        
    db.commit()
    
    # 2. Re-Index Vector
    # We need content content.
    try:
        crawl = db.query(CrawlResult).filter(CrawlResult.item_id == id).first()
        content_snippet = ""
        if crawl and crawl.html_content_path:
             # Resolve path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            # Handle if path starts with data/ or not
            rel_path = crawl.html_content_path
            if rel_path.startswith("/"):
                 full_path = rel_path
            else:
                 full_path = os.path.join(base_dir, rel_path)
            
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content_snippet = f.read()[:1000]
        
        # Combine summary + Evidence
        rich_summary = f"Summary: {analysis.summary}\n\nEvidence: {content_snippet}"
        
        vector_service.add_item(
            fqdn=item.fqdn,
            content_summary=rich_summary,
            category=analysis.category_main,
            is_malicious=analysis.is_malicious
        )
        
        db.add(PipelineLog(item_id=id, stage="KB_MANUAL", level="INFO", message="Updated and Re-indexed via KB Manager"))
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to re-index {item.fqdn}: {e}")
        # Don't fail the request, but log it
        
    return {"status": "success", "message": "Updated and Re-indexed"}

@router.post("/items/{id}/rebuild")
def rebuild_kb_item(id: int, db: Session = Depends(get_db)):
    """
    Force Re-Index Vector from existing SQL data.
    """
    # Logic is same as update basically, but without changing fields
    # Just reusing the update logic with no changes
    return update_kb_item(id, KBUpdateRequest(), db)

@router.delete("/items/{id}")
def delete_kb_item(id: int, db: Session = Depends(get_db)):
    """
    Soft delete or Hide?
    For now, let's just set status to ARCHIVED and remove from Vector.
    """
    item = db.query(PipelineItem).filter(PipelineItem.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # Remove from Vector
    try:
        # Chroma doesn't have easy delete by ID in our wrapper yet?
        # vector_service.collection.delete(ids=[item.fqdn])
        if vector_service.collection:
            vector_service.collection.delete(ids=[item.fqdn])
    except Exception as e:
        logger.error(f"Failed to delete vector for {item.fqdn}: {e}")
        
    item.status = PipelineStatus.ARCHIVED
    db.commit()
    
    return {"status": "success", "message": "Archived and removed from active KB"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.pipeline import PipelineItem, PipelineStatus, PipelineLog
from app.models.schemas import PipelineItemResponse, PipelineItemCreate, PipelineStats, SystemHealth, ComponentStatus
from sqlalchemy import func

router = APIRouter()

@router.get("/stats", response_model=PipelineStats)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(PipelineItem).count()
    status_counts = db.query(PipelineItem.status, func.count(PipelineItem.status)).group_by(PipelineItem.status).all()
    
    # Fetch Recent Activity
    recent_items = db.query(PipelineItem).order_by(PipelineItem.updated_at.desc()).limit(10).all()
    recent_logs = db.query(PipelineLog).order_by(PipelineLog.id.desc()).limit(10).all()
    
    return {
        "total": total,
        "by_status": {status: count for status, count in status_counts},
        "recent_items": recent_items,
        "recent_logs": recent_logs
    }

@router.get("/items", response_model=List[PipelineItemResponse])
def get_items(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(PipelineItem)
    if status:
        query = query.filter(PipelineItem.status == status)
    if search:
        query = query.filter(PipelineItem.fqdn.contains(search))
    
    # Eager load relationships for performance
    from sqlalchemy.orm import joinedload
    query = query.options(joinedload(PipelineItem.crawl_result), joinedload(PipelineItem.analysis_result))
    
    return query.order_by(PipelineItem.updated_at.desc()).offset(skip).limit(limit).all()

@router.post("/items", response_model=PipelineItemResponse)
def create_item(item: PipelineItemCreate, db: Session = Depends(get_db)):
    db_item = PipelineItem(**item.dict(), status=PipelineStatus.DISCOVERED)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.post("/control/flush_failed")
def flush_failed(db: Session = Depends(get_db)):
    """Reset failed items to QUEUED"""
    updated = db.query(PipelineItem).filter(
        PipelineItem.status.in_([PipelineStatus.CRAWLED_FAIL, PipelineStatus.ANALYSIS_FAIL])
    ).update({PipelineItem.status: PipelineStatus.QUEUED}, synchronize_session=False)
    db.commit()
@router.get("/stats/bottlenecks")
def get_bottlenecks(db: Session = Depends(get_db)):
    """
    Identify items stuck in active states for too long.
    Thresholds:
    - CRAWLING: > 5 minutes
    - ANALYZING: > 5 minutes
    """
    import datetime
    
    now = datetime.datetime.now()
    threshold = now - datetime.timedelta(minutes=5)
    
    stuck_crawling = db.query(PipelineItem).filter(
        PipelineItem.status == PipelineStatus.CRAWLING,
        PipelineItem.updated_at < threshold
    ).count()
    
    stuck_analyzing = db.query(PipelineItem).filter(
        PipelineItem.status == PipelineStatus.ANALYZING,
        PipelineItem.updated_at < threshold
    ).count()
    
    # Get details of stuck items (limit 10 for preview)
    stuck_items = db.query(PipelineItem).filter(
        PipelineItem.status.in_([PipelineStatus.CRAWLING, PipelineStatus.ANALYZING]),
        PipelineItem.updated_at < threshold
    ).limit(10).all()
    
    return {
        "stuck_crawling_count": stuck_crawling,
        "stuck_analyzing_count": stuck_analyzing,
        "sample_stuck_items": stuck_items
    }

@router.get("/health", response_model=SystemHealth)
def get_system_health(db: Session = Depends(get_db)):
    """
    Detailed system health check for all components
    """
    from app.services.orchestrator import orchestrator
    from app.services.llm_service import llm_service
    from sqlalchemy import text  # Import text for SQL query
    import datetime
    
    now = datetime.datetime.now()
    components = []
    
    # 1. Orchestrator
    orch_status = orchestrator.get_status()
    components.append(ComponentStatus(
        name="Orchestrator",
        status="operational" if orch_status["is_running"] else "stopped",
        details=f"Uptime: {int(orch_status['uptime_seconds'])}s",
        last_check=now
    ))
    
    # 2. Crawler Loop
    last_crawl = orch_status["last_crawl_run"]
    crawl_status = "operational"
    crawl_details = "Running normally"
    if not last_crawl:
        crawl_status = "unknown"
        crawl_details = "No run recorded"
    elif (now - last_crawl).total_seconds() > 60:
        crawl_status = "degraded"
        crawl_details = f"Last run {int((now - last_crawl).total_seconds())}s ago (Stalled?)"
    
    components.append(ComponentStatus(
        name="Crawler Loop",
        status=crawl_status,
        details=crawl_details,
        last_check=last_crawl if last_crawl else now
    ))

    # 3. Analysis Loop
    last_analysis = orch_status["last_analysis_run"]
    analysis_status = "operational"
    analysis_details = "Running normally"
    if not last_analysis:
        analysis_status = "unknown"
        analysis_details = "No run recorded"
    elif (now - last_analysis).total_seconds() > 30:
        analysis_status = "degraded"
        analysis_details = f"Last run {int((now - last_analysis).total_seconds())}s ago (Slow?)"
        
    components.append(ComponentStatus(
        name="Analysis Loop",
        status=analysis_status,
        details=analysis_details,
        last_check=last_analysis if last_analysis else now
    ))
    
    # 4. LLM Service
    llm_health = "operational"
    llm_msg = f"Connected to {llm_service.model}"
    if not llm_service.base_url:
        llm_health = "down"
        llm_msg = "No active connection"
    elif "106.254.248.154" in llm_service.base_url:
        llm_msg += " (External Relay)"
    else:
        llm_msg += " (Direct)"
        
    components.append(ComponentStatus(
        name="LLM Service",
        status=llm_health,
        details=llm_msg,
        last_check=now
    ))
    
    # 5. Database
    try:
        db.execute(text("SELECT 1"))
        db_status = "operational"
        db_details = "Connection active"
    except Exception as e:
        db_status = "down"
        db_details = str(e)
        
    components.append(ComponentStatus(
        name="Database (SQLite)",
        status=db_status,
        details=db_details,
        last_check=now
    ))
    
    # 6. Health Monitor
    from app.services.health_monitor import health_monitor
    hm_status = "operational" if health_monitor.is_running else "stopped"
    hm_details = f"Last Crawl Check: {health_monitor.last_activity['crawl'].strftime('%H:%M:%S')}"
    
    components.append(ComponentStatus(
        name="Auto-Recovery Monitor",
        status=hm_status,
        details=hm_details,
        last_check=datetime.datetime.now()
    ))
    
    # Overall Status
    system_status = "healthy"
    for c in components:
        if c.status == "down":
            system_status = "critical"
            break
        if c.status == "degraded":
            system_status = "degraded"
            
    return SystemHealth(
        status=system_status,
        components=components
    )

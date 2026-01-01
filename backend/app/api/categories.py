from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.core.database import get_db
from app.models.category import CategoryDefinition
from app.models.pipeline import AnalysisResult
from app.services.vector_service import vector_service # For async updates (later)

router = APIRouter()

# --- Schemas ---
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_system: bool
    count: Optional[int] = 0

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """List all defined categories with usage counts."""
    cats = db.query(CategoryDefinition).order_by(CategoryDefinition.name).all()
    
    # Calculate usage
    from sqlalchemy import func
    usage = db.query(AnalysisResult.category_main, func.count(AnalysisResult.id))\
              .group_by(AnalysisResult.category_main).all()
    usage_map = {c: count for c, count in usage}
    
    results = []
    for c in cats:
        resp = CategoryResponse.model_validate(c)
        resp.count = usage_map.get(c.name, 0)
        results.append(resp)
        
    return results

@router.post("/", response_model=CategoryResponse)
def create_category(cat: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category."""
    existing = db.query(CategoryDefinition).filter(CategoryDefinition.name == cat.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
        
    new_cat = CategoryDefinition(name=cat.name, description=cat.description)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

@router.put("/{id}", response_model=CategoryResponse)
def update_category(id: int, update: CategoryUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Rename/Update a category.
    TRIGGERS CASCADE UPDATE on AnalysisResults!
    """
    cat = db.query(CategoryDefinition).filter(CategoryDefinition.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    old_name = cat.name
    new_name = update.name
    
    # Check duplicate name
    if old_name != new_name:
        existing = db.query(CategoryDefinition).filter(CategoryDefinition.name == new_name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category name already exists")
            
    cat.name = new_name
    cat.description = update.description
    db.commit()
    
    if old_name != new_name:
        # Cascade Update: SQL
        # This is a synchronous update on SQL (fast for <100k usually, but ideally async)
        background_tasks.add_task(cascade_category_update, old_name, new_name, db)

    return cat

@router.delete("/{id}")
def delete_category(id: int, db: Session = Depends(get_db)):
    """
    Delete a category. 
    Only allowed if Usage is 0? Or force move to Uncategorized?
    For safety: Only allowed if usage is 0.
    """
    cat = db.query(CategoryDefinition).filter(CategoryDefinition.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    if cat.is_system:
        raise HTTPException(status_code=400, detail="System categories cannot be deleted")

    # Check usage
    count = db.query(AnalysisResult).filter(AnalysisResult.category_main == cat.name).count()
    if count > 0:
         raise HTTPException(status_code=400, detail=f"Cannot delete category '{cat.name}' because it is used by {count} items. Please rename or reassign items first.")

    db.delete(cat)
    db.commit()
    return {"status": "success"}

# --- Background Task Implementation ---
def cascade_category_update(old_name: str, new_name: str, db: Session):
    """
    1. Update AnalysisResults (bulk)
    2. Re-index Vector (Async/Slow - placeholder for now or lightweight)
    """
    # 1. SQL Update
    try:
        # New session needed strictly speaking if passed session is closed, but Depends(get_db) session closes after request.
        # So we technically need a new session context here or use raw engine.
        # For simplicity in this logical block, let's assume we create a new session:
        from app.core.database import SessionLocal
        bg_db = SessionLocal()
        
        updated_count = bg_db.query(AnalysisResult)\
                             .filter(AnalysisResult.category_main == old_name)\
                             .update({AnalysisResult.category_main: new_name}, synchronize_session=False)
        bg_db.commit()
        print(f"Cascade Update: Renamed {old_name} -> {new_name} for {updated_count} items in SQL.")
        
        # 2. Vector Update (Costly)
        # Strategy: We can't query Chroma by Metadata in mass update easily efficiently without iterating.
        # For prototype, we might skip this or do it lazy.
        # Ideally: vector_service.update_category(old_name, new_name)
        
        bg_db.close()
    except Exception as e:
        print(f"Error in cascade update: {e}")

@router.get("/stats")
def get_category_stats(db: Session = Depends(get_db)):
    """
    Return distribution of categories.
    """
    from sqlalchemy import func
    total = db.query(AnalysisResult).count()
    usage = db.query(AnalysisResult.category_main, func.count(AnalysisResult.id))\
              .group_by(AnalysisResult.category_main)\
              .order_by(func.count(AnalysisResult.id).desc()).all()
    
    stats = []
    for cat, count in usage:
        stats.append({
            "name": cat,
            "count": count,
            "percent": round((count / total * 100), 1) if total > 0 else 0
        })
        
    return {
        "total_items": total,
        "categories": stats
    }

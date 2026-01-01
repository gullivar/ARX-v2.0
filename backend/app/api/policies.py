from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.pipeline import DomainFilter
from app.models.schemas import DomainFilterCreate, DomainFilterResponse

router = APIRouter()

@router.get("/", response_model=List[DomainFilterResponse])
def get_policies(db: Session = Depends(get_db)):
    return db.query(DomainFilter).all()

@router.post("/", response_model=DomainFilterResponse)
def create_policy(policy: DomainFilterCreate, db: Session = Depends(get_db)):
    db_policy = DomainFilter(**policy.dict())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy

@router.delete("/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(DomainFilter).filter(DomainFilter.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(policy)
    db.commit()
    return {"message": "Deleted"}

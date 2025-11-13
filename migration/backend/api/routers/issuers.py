"""
Issuers (Profiles) API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from backend.db import get_db
from backend.db.models import Profile
from backend.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_issuers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all issuers/profiles"""
    issuers = db.query(Profile).offset(skip).limit(limit).all()
    return {"issuers": issuers, "total": len(issuers)}


@router.get("/{issuer_id}")
async def get_issuer(
    issuer_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific issuer/profile"""
    issuer = db.query(Profile).filter(Profile.id == issuer_id).first()
    if not issuer:
        raise HTTPException(status_code=404, detail="Issuer not found")
    return issuer


@router.post("/")
async def create_issuer(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new issuer/profile"""
    return {"message": "Issuer creation endpoint - to be implemented"}


@router.put("/{issuer_id}")
async def update_issuer(
    issuer_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an issuer/profile"""
    return {"message": "Issuer update endpoint - to be implemented"}


@router.delete("/{issuer_id}")
async def delete_issuer(
    issuer_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an issuer/profile"""
    return {"message": "Issuer deletion endpoint - to be implemented"}


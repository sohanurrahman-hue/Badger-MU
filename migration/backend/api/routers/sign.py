"""
Signing API Router
Handles credential signing and verification
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from backend.db import get_db
from backend.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
async def sign_credential(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Sign a credential with cryptographic proof"""
    return {"message": "Credential signing endpoint - to be implemented"}


@router.post("/verify")
async def verify_credential(
    db: Session = Depends(get_db)
):
    """Verify a signed credential"""
    return {"message": "Credential verification endpoint - to be implemented"}


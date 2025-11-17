"""
Achievements API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import uuid

from backend.db import get_db
from backend.db.models import (
    Achievement, RelatedAchievement, ResultDescription, 
    Alignment, IdentifierEntry, Image, Profile, IssuedBadge
)
from backend.auth.middleware import get_current_user
from backend.schemas.open_badges.achievement import AchievementSchema
from backend.db.models import AchievementTypeEnum
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse


logger = logging.getLogger(__name__)

router = APIRouter()

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import base64
import jwt
from datetime import datetime, timezone
from pathlib import Path


# === RSA helpers ===

def _b64url_no_pad(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")

def _int_to_b64url(n: int) -> str:
    return _b64url_no_pad(n.to_bytes((n.bit_length() + 7) // 8, "big"))

def get_rsa_private_key():
    """
    Load an RSA private key from backend/private_key.pem.
    The PEM must contain an RSA key (PKCS#8 or PKCS#1). No password.
    """
    backend_dir = Path(__file__).parent.parent.parent  # .../backend
    private_key_path = backend_dir / "private_key.pem"

    try:
        with open(private_key_path, "rb") as f:
            pem = f.read()
    except FileNotFoundError:
        raise RuntimeError(
            f"private_key.pem not found at {private_key_path}. "
            "Generate an RSA keypair and save it there."
        )

    key = serialization.load_pem_private_key(pem, password=None)
    # Guard: must be RSA
    if not isinstance(key, rsa.RSAPrivateKey):
        raise RuntimeError(
            "private_key.pem is not an RSA private key. "
            "Either replace it with an RSA key or switch algorithm to EdDSA."
        )
    return key

def get_rsa_public_key():
    return get_rsa_private_key().public_key()

def get_rsa_jwk_public() -> dict:
    """
    Build a public RSA JWK {kty:'RSA', n:'...', e:'AQAB'} from the loaded RSA key.
    """
    pub = get_rsa_public_key()
    numbers = pub.public_numbers()
    e = numbers.e
    n = numbers.n
    return {
        "kty": "RSA",
        "n": _int_to_b64url(n),
        "e": _int_to_b64url(e),
    }

def get_rsa_headers() -> dict:
    """
    Full JWT header for RS256 with embedded JWK (so validators can verify w/o JWKS).
    """
    return {
        "alg": "RS256",
        "typ": "JWT",
        "jwk": get_rsa_jwk_public(),
    }


# --- FIXED SCHEMAS AND ENDPOINTS ---
class IssueBadgeRequest(BaseModel):
    recipient_id: Optional[str] = None  # <-- **FIX:** Added recipient ID
    organization_name: str
    organization_id: str
    achievement_name: str
    achievement_type: str
    narrative: str
    description: str
    achievement_id: str  # This is the ID for the *achievement template*


@router.post("/issue-vc-jwt", status_code=status.HTTP_201_CREATED)
async def issue_badge_as_jwt_rs256(
    request: IssueBadgeRequest,
    db: Session = Depends(get_db)
):
    """
    Issues a new badge as a VC-JWT using RS256 (RSA).
    Saves the JWT to the database for later retrieval.
    """
    domain = "https://nondisbursed-yanira-stampedingly.ngrok-free.dev"
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DOMAIN environment variable not set"
        )

    badge_id = uuid.uuid4()

    # Public URL for the credential (must match your GET endpoint path)
    public_url = f"{domain}/api/achievements/credentials/{badge_id}"

    # RFC3339 'Z' time
    validFrom = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    validUntil = (datetime.now(timezone.utc) + timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')
    # Minimal OB 3.0-esque payload (you can expand as needed)
    jwt_payload = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json"
        ],
        "id": public_url,
        "type": ["VerifiableCredential", "OpenBadgeCredential"],
        "issuer": {
            "id": f"{domain}/issuers/{request.organization_id}",
            "type": ["Profile"],
            "name": request.organization_name
        },
        "validFrom": validFrom,
        "validUntil": validUntil,
        "name": request.achievement_name,
        "credentialSubject": {
            "id": request.recipient_id,
            "type": ["AchievementSubject"],
            "achievement": {
                "id": f"{domain}/achievements/{request.achievement_id}",
                "type": [request.achievement_type],
                "criteria": {"narrative": request.narrative},
                "description": request.description,
                "name": request.achievement_name
            }
        },

        # Standard JWT claims that many tools expect:
        "iss": f"{domain}/issuers/{request.organization_id}",
        "sub": request.recipient_id,
        "jti": public_url,
    }

    # Load RSA private key and sign with RS256; include proper header with embedded JWK
    private_key = get_rsa_private_key()
    vc_jwt_string = jwt.encode(
        jwt_payload,
        private_key,
        algorithm="RS256",
        headers=get_rsa_headers()
    )

    issued_badge = IssuedBadge(
        id=badge_id,
        jwt_string=vc_jwt_string,
        achievement_id=request.achievement_id,
        organization_id=request.organization_id,
        recipient_id=request.recipient_id
    )
    db.add(issued_badge)
    db.commit()
    db.refresh(issued_badge)

    return {
        "message": "VC-JWT (RS256) created successfully",
        "badge_jwt": vc_jwt_string,
        "badge_uuid": str(issued_badge.id),
        "credential_url": public_url
    }



@router.get(
    "/credentials/{badge_uuid}",
    response_class=PlainTextResponse # Tell FastAPI to return as raw text
)
async def get_issued_badge(
    badge_uuid: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Serves the publicly verifiable badge (as a JWS string).
    This is the URL you give to the validator.
    """
    
    # This query will now work because you're saving the 'id=badge_uuid'
    badge = db.query(IssuedBadge).filter(IssuedBadge.id == badge_uuid).first()
    
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Badge not found"
        )

    # Return the raw JWS string (the badge)
    return badge.jwt_string



@router.get("/")
async def list_achievements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all achievements"""
    achievements = db.query(Achievement).offset(skip).limit(limit).all()
    return {"achievements": achievements, "total": len(achievements)}


@router.get("/{achievement_id}")
async def get_achievement(
    achievement_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific achievement"""
    achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return achievement



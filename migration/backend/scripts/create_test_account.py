#!/usr/bin/env python3
"""
Script to create a dummy test account for development/testing

Usage:
    python scripts/create_test_account.py

This script creates a test user and profile (issuer) in the database
for local development and testing purposes.
"""
import sys
import os
from pathlib import Path

# Add parent directory (migration/) to path to import backend modules
# This allows 'from backend.db import ...' to work
backend_dir = Path(__file__).parent.parent  # backend/
parent_dir = backend_dir.parent  # migration/
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from sqlalchemy.orm import Session
from backend.db import get_db, init_db
from backend.db.models import User, Profile
import uuid
from datetime import datetime, timezone


def create_test_account(db: Session):
    """Create a test user and issuer profile"""
    
    # Create test user
    test_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="test@badgeengine.local",
        name="Test User",
        email_verified=True,
        is_active=True,
        is_super_user=True,
        role="admin",
        last_login=datetime.now(timezone.utc)
    )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == test_user.email).first()
    if existing_user:
        print(f"⚠️  User {test_user.email} already exists. Skipping user creation.")
        user = existing_user
    else:
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Created test user: {test_user.email} (ID: {test_user.id})")
        user = test_user
    
    # Create test issuer profile
    test_profile = Profile(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        iri="https://badgeengine.local/issuers/test",
        type=["Profile"],
        name="Test Issuer Organization",
        email="issuer@badgeengine.local",
        email_verified=True,
        description="A test issuer organization for development and testing",
        url="https://badgeengine.local",
        phone="+1-555-0100",
        is_active=True,
        is_public=True,
        role="issuer"
    )
    
    # Check if profile already exists
    existing_profile = db.query(Profile).filter(Profile.iri == test_profile.iri).first()
    if existing_profile:
        print(f"⚠️  Profile {test_profile.iri} already exists. Skipping profile creation.")
        profile = existing_profile
    else:
        db.add(test_profile)
        db.commit()
        db.refresh(test_profile)
        print(f"✅ Created test issuer profile: {test_profile.name} (ID: {test_profile.id})")
        profile = test_profile
    
    # Create additional test users for different roles
    issuer_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        email="issuer@badgeengine.local",
        name="Issuer User",
        email_verified=True,
        is_active=True,
        is_super_user=False,
        role="issuer",
        last_login=datetime.now(timezone.utc)
    )
    
    existing_issuer = db.query(User).filter(User.email == issuer_user.email).first()
    if not existing_issuer:
        db.add(issuer_user)
        db.commit()
        print(f"✅ Created issuer user: {issuer_user.email}")
    
    # Create regular user
    regular_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000004"),
        email="user@badgeengine.local",
        name="Regular User",
        email_verified=True,
        is_active=True,
        is_super_user=False,
        role="user",
        last_login=datetime.now(timezone.utc)
    )
    
    existing_regular = db.query(User).filter(User.email == regular_user.email).first()
    if not existing_regular:
        db.add(regular_user)
        db.commit()
        print(f"✅ Created regular user: {regular_user.email}")
    
    db.commit()
    
    print("\n" + "="*60)
    print("Test Accounts Created Successfully!")
    print("="*60)
    print("\nTest User Accounts:")
    print(f"  Admin User:")
    print(f"    Email: {user.email}")
    print(f"    Password: (N/A - uses Entra ID SSO)")
    print(f"    Role: {user.role}")
    print(f"    Super User: {user.is_super_user}")
    print(f"\n  Issuer User:")
    print(f"    Email: {issuer_user.email}")
    print(f"    Role: {issuer_user.role}")
    print(f"\n  Regular User:")
    print(f"    Email: {regular_user.email}")
    print(f"    Role: {regular_user.role}")
    print(f"\nTest Issuer Profile:")
    print(f"    Name: {profile.name}")
    print(f"    IRI: {profile.iri}")
    print(f"    Email: {profile.email}")
    print("\n" + "="*60)
    print("Note: These accounts are for development/testing only.")
    print("In production, users are created via Entra ID SSO authentication.")
    print("="*60 + "\n")


def main():
    """Main entry point"""
    print("Creating test accounts...")
    print("-" * 60)
    
    # Initialize database (create tables if they don't exist)
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    # Create test accounts
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        create_test_account(db)
    except Exception as e:
        print(f"❌ Error creating test accounts: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()


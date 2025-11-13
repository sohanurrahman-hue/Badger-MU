"""
Achievements API Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
import uuid

from backend.db import get_db
from backend.db.models import (
    Achievement, RelatedAchievement, ResultDescription, 
    Alignment, IdentifierEntry, Image, Profile
)
from backend.auth.middleware import get_current_user
from backend.schemas.open_badges.achievement import AchievementSchema


logger = logging.getLogger(__name__)

router = APIRouter()


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


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_achievement(
    achievement_data: AchievementSchema,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)
):
    """
    Create a new achievement
    
    Maps AchievementSchema fields to Achievement model:
    - Schema uses camelCase (e.g., achievementType, creditsAvailable)
    - Model uses snake_case (e.g., achievement_type, credits_available)
    - Nested objects (alignment, related, resultDescription) are handled separately
    """
    try:
        # Check if IRI already exists
        existing = db.query(Achievement).filter(Achievement.iri == achievement_data.id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Achievement with IRI '{achievement_data.id}' already exists"
            )
        
        # Handle creator - get creator_id from creator profile if provided
        creator_id = None
        if achievement_data.creator:
            if achievement_data.creator.id:
                # Creator is a URL/IRI - try to find existing profile
                creator_profile = db.query(Profile).filter(Profile.iri == achievement_data.creator.id).first()
                if creator_profile:
                    creator_id = creator_profile.id
                else:
                    # TODO: Create profile from creator schema if needed
                    logger.warning(f"Creator profile not found for IRI: {achievement_data.creator.id}")
            # If creator is a full ProfileSchema object, we'd need to create/update it
            # For now, we'll use the current user as creator if no creator_id found
            # if not creator_id:
            #     # Use current user's profile as creator
            #     user_profile = db.query(Profile).filter(Profile.email == current_user.get("email")).first()
            #     if user_profile:
            #         creator_id = user_profile.id
        
        # Handle image - get image_id from image if provided
        image_id = None
        if achievement_data.image:
            if achievement_data.image.id:
                # Image is a URL/IRI - try to find existing image
                existing_image = db.query(Image).filter(Image.iri == achievement_data.image.id).first()
                if existing_image:
                    image_id = existing_image.id
                else:
                    # Create new image from schema
                    new_image = Image(
                        iri=achievement_data.image.id,
                        type=achievement_data.image.type if hasattr(achievement_data.image, 'type') else ["Image"],
                        caption=achievement_data.image.caption if hasattr(achievement_data.image, 'caption') else None,
                        encoded_image_data=achievement_data.image.id if hasattr(achievement_data.image, 'id') else None
                    )
                    db.add(new_image)
                    db.flush()  # Get the ID
                    image_id = new_image.id
        
        # Convert criteria schema to dict for JSONB storage
        criteria_dict = achievement_data.criteria.model_dump(exclude_none=True)
        
        # Convert endorsementJwt to list of dicts if provided
        endorsement_jwt = None
        if achievement_data.endorsementJwt:
            endorsement_jwt = [jwt.model_dump() if hasattr(jwt, 'model_dump') else jwt for jwt in achievement_data.endorsementJwt]
        
        # Create the achievement
        achievement = Achievement(
            id=uuid.uuid4(),  # Generate new UUID
            iri=achievement_data.id,
            type=achievement_data.type,  # JSONB array
            achievement_type=achievement_data.achievementType,  # Enum
            name=achievement_data.name,
            description=achievement_data.description,
            criteria=criteria_dict,  # JSONB dict
            credits_available=achievement_data.creditsAvailable,
            field_of_study=achievement_data.fieldOfStudy,
            human_code=achievement_data.humanCode,
            in_language=achievement_data.inLanguage,
            specialization=achievement_data.specialization,
            tags=achievement_data.tag,  # Schema uses 'tag', model uses 'tags'
            version=achievement_data.version,
            is_public=False,  # Default to private
            endorsement_jwt=endorsement_jwt,  # JSONB array
            creator_id=creator_id,
            image_id=image_id
        )
        
        db.add(achievement)
        db.flush()  # Get the achievement ID for related objects
        
        # Handle related achievements
        if achievement_data.related:
            for related_schema in achievement_data.related:
                related = RelatedAchievement(
                    achievement_id=achievement.id,
                    related_iri=related_schema.id,
                    type=related_schema.type,
                    in_language=related_schema.inLanguage,
                    version=related_schema.version
                )
                db.add(related)
        
        # Handle result descriptions
        if achievement_data.resultDescription:
            from backend.db.models import ResultTypeEnum
            for result_desc_schema in achievement_data.resultDescription:
                result_desc = ResultDescription(
                    iri=result_desc_schema.id,
                    type=result_desc_schema.type,
                    name=result_desc_schema.name,
                    result_type=result_desc_schema.resultType,  # Enum
                    allowed_value=result_desc_schema.allowedValue,
                    required_level=result_desc_schema.requiredLevel,
                    required_value=result_desc_schema.requiredValue,
                    value_min=result_desc_schema.valueMin,
                    value_max=result_desc_schema.valueMax,
                    achievement_id=achievement.id
                )
                db.add(result_desc)
                
                # Handle rubric criterion levels if present
                if result_desc_schema.rubricCriterionLevel:
                    from backend.db.models import RubricCriterionLevel
                    for rubric_level_schema in result_desc_schema.rubricCriterionLevel:
                        rubric_level = RubricCriterionLevel(
                            iri=rubric_level_schema.id,
                            type=rubric_level_schema.type,
                            name=rubric_level_schema.name,
                            description=rubric_level_schema.description,
                            level=rubric_level_schema.level,
                            points=rubric_level_schema.points,
                            result_description_id=result_desc.id
                        )
                        db.add(rubric_level)
        
        # Handle alignments (many-to-many relationship)
        if achievement_data.alignment:
            for alignment_schema in achievement_data.alignment:
                # Check if alignment already exists
                existing_alignment = db.query(Alignment).filter(
                    Alignment.target_url == alignment_schema.targetUrl
                ).first()
                
                if not existing_alignment:
                    from backend.db.models import AlignmentTargetTypeEnum
                    alignment = Alignment(
                        type=alignment_schema.type,
                        target_name=alignment_schema.targetName,
                        target_url=alignment_schema.targetUrl,
                        target_description=alignment_schema.targetDescription,
                        target_framework=alignment_schema.targetFramework,
                        target_code=alignment_schema.targetCode,
                        target_type=alignment_schema.targetType if hasattr(alignment_schema, 'targetType') else None
                    )
                    db.add(alignment)
                    db.flush()
                    achievement.alignments.append(alignment)
                else:
                    achievement.alignments.append(existing_alignment)
        
        # Handle other identifiers
        if achievement_data.otherIdentifier:
            for identifier_schema in achievement_data.otherIdentifier:
                identifier = IdentifierEntry(
                    type=identifier_schema.type,
                    identifier=identifier_schema.identifier,
                    identifier_type=identifier_schema.identifierType,  # Required field
                    achievement_id=achievement.id
                )
                db.add(identifier)
        
        db.commit()
        db.refresh(achievement)
        
        logger.info(f"Created achievement '{achievement.name}' (ID: {achievement.id}) successfully.")
        
        return {
            "id": str(achievement.id),
            "iri": achievement.iri,
            "name": achievement.name,
            "message": "Achievement created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error creating achievement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create achievement: {str(e)}"
        )


@router.put("/{achievement_id}")
async def update_achievement(
    achievement_id: str,
    # achievement_data: AchievementUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an achievement"""
    # TODO: Implement achievement update
    return {"message": "Achievement update endpoint - to be implemented"}


@router.delete("/{achievement_id}")
async def delete_achievement(
    achievement_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an achievement"""
    # TODO: Implement achievement deletion
    return {"message": "Achievement deletion endpoint - to be implemented"}


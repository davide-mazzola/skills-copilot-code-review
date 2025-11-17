"""
Announcement endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..database import announcements_collection
from ..database import teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

def require_auth(username: Optional[str] = None) -> Dict[str, Any]:
    """Dependency to require authentication for management endpoints."""
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required.")
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid user.")
    return teacher

@router.get("", response_model=List[Dict[str, Any]])
def get_announcements() -> List[Dict[str, Any]]:
    """Get all current (non-expired) announcements."""
    now = datetime.now()
    announcements = list(announcements_collection.find({
        "expiration": {"$gte": now}
    }))
    for ann in announcements:
        ann["id"] = str(ann.pop("_id"))
    return announcements

@router.post("", response_model=Dict[str, Any])
def create_announcement(
    message: str,
    expiration: datetime,
    start_date: Optional[datetime] = None,
    username: str = Depends(require_auth)
) -> Dict[str, Any]:
    """Create a new announcement (auth required)."""
    ann = {
        "message": message,
        "expiration": expiration,
        "start_date": start_date
    }
    result = announcements_collection.insert_one(ann)
    ann["id"] = str(result.inserted_id)
    return ann

@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    message: Optional[str] = None,
    expiration: Optional[datetime] = None,
    start_date: Optional[datetime] = None,
    username: str = Depends(require_auth)
) -> Dict[str, Any]:
    """Update an announcement (auth required)."""
    update_fields = {}
    if message is not None:
        update_fields["message"] = message
    if expiration is not None:
        update_fields["expiration"] = expiration
    if start_date is not None:
        update_fields["start_date"] = start_date
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update.")
    result = announcements_collection.update_one(
        {"_id": announcement_id}, {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    ann = announcements_collection.find_one({"_id": announcement_id})
    ann["id"] = str(ann.pop("_id"))
    return ann

@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    username: str = Depends(require_auth)
):
    """Delete an announcement (auth required)."""
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return {"success": True}

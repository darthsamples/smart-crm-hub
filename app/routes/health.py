from fastapi import APIRouter
from app.database import get_db_connection

router = APIRouter()

@router.get("/health/")
async def health_check():
    try:
        with get_db_connection():
            return {"status": "healthy"}
    except Exception:
        return {"status": "unhealthy"}
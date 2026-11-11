from fastapi import APIRouter

from app.api.v1 import publishers

router = APIRouter(prefix="/api/v1")
router.include_router(publishers.router)

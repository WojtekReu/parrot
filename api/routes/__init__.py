from api.routes.v2 import router as v2_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(v2_router)

from fastapi import APIRouter

from .futbol import router as futbol_router
from .nba import router as nba_router
from .ws import router as ws_router

router = APIRouter()

router.include_router(futbol_router)
router.include_router(nba_router)
router.include_router(ws_router)

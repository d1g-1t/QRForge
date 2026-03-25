from fastapi import APIRouter

from qrcode_service.api.v1.generate import router as generate_router
from qrcode_service.api.v1.codes import router as codes_router
from qrcode_service.api.v1.scan import router as scan_router
from qrcode_service.api.v1.analytics import router as analytics_router

router = APIRouter()
router.include_router(generate_router, prefix="/api/v1", tags=["generation"])
router.include_router(codes_router, prefix="/api/v1", tags=["codes"])
router.include_router(scan_router, tags=["scan"])
router.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])

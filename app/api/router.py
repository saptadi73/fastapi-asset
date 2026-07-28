from fastapi import APIRouter

from app.modules.assets.routes import router as assets_router
from app.modules.attachments.routes import router as attachments_router
from app.modules.auth.routes import router as auth_router
from app.modules.leases.routes import router as leases_router
from app.modules.maintenance.routes import router as maintenance_router
from app.modules.partners.routes import router as partners_router
from app.modules.software_licenses.routes import router as software_licenses_router
from app.modules.tracking.routes import router as tracking_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(partners_router, tags=["Business Partners"])
api_router.include_router(assets_router, tags=["Asset Registry"])
api_router.include_router(attachments_router, tags=["Attachments"])
api_router.include_router(leases_router, tags=["Leases"])
api_router.include_router(software_licenses_router, tags=["Software Licenses"])
api_router.include_router(maintenance_router, tags=["Maintenance"])
api_router.include_router(tracking_router, tags=["Tracking & Stocktake"])

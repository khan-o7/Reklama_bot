from .auth_routes import router as auth_router
from .dashboard_routes import router as dashboard_router
from .api_routes import router as api_router

__all__ = ["auth_router", "dashboard_router", "api_router"]

from .start import router as start_router
from .admin import router as admin_router
from .moderation import router as moderation_router
from .group_events import router as group_events_router

__all__ = [
    "start_router",
    "admin_router",
    "moderation_router",
    "group_events_router",
]

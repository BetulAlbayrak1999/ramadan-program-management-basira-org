from app.routes.auth import router as auth_router
from app.routes.participant import router as participant_router
from app.routes.supervisor import router as supervisor_router
from app.routes.admin import router as admin_router
from app.routes.settings import router as settings_router

all_routers = [
    auth_router,
    participant_router,
    supervisor_router,
    admin_router,
    settings_router,
]

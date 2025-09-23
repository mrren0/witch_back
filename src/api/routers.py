from src.api.users import router as user_router
from src.api.products import router as product_router
from src.api.beeline import router as auth_router

# новые строки ⬇
from src.api.events import router as events_router
from src.api.prizes import router as prizes_router
from src.api.system import router as system_router

all_routers = [
    user_router,
    product_router,
    auth_router,
    events_router,
    prizes_router,
    system_router,
]

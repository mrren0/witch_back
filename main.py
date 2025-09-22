from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware

from src.api.routers import all_routers

# ─── Swagger метаданные ───────────────────────────────────────────────
tags_metadata = [
    {"name": "Auth",    "description": "Авторизация и платежи"},
    {"name": "User",    "description": "Профиль игрока и ресурсы"},
    {"name": "Product", "description": "Каталог магазинов"},
    {"name": "Events",  "description": "Соревнования и лидерборды"},
    {"name": "Prizes",  "description": "Незабранные награды"},
]

token_scheme = APIKeyHeader(name="accessToken")

app = FastAPI(
    title="SurviveAPI",
    version="0.1.0",
    docs_url="/docs",
    openapi_tags=tags_metadata,
    debug=True,
)

# ─── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ─── маршруты ─────────────────────────────────────────────────────────
for router in all_routers:
    app.include_router(router)

# ─── примеры cURL прямо в Swagger ─────────────────────────────────────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        tags=tags_metadata,
    )
    schema["paths"]["/api/user"]["get"]["x-codeSamples"] = [
        {
            "lang": "bash",
            "label": "cURL",
            "source": "curl -H 'accessToken: <TOKEN>' http://localhost:8082/api/user",
        }
    ]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

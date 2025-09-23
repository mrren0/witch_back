import pytz

from src.api.APIRouter import APIRouter
from src.infra.create_time import Time

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/time")
async def get_system_time() -> dict[str, str]:
    """Return current UTC time in ISO 8601 format."""
    moscow_now = Time().now()
    utc_now = moscow_now.astimezone(pytz.UTC)
    return {"utc_time": utc_now.isoformat()}

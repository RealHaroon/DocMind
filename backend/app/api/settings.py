from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.db.database import connect
from app.schemas.settings import AppSettingsResponse, AppSettingsUpdate


router = APIRouter(prefix="/settings", tags=["settings"])


def _response(row: object, settings: Settings) -> AppSettingsResponse:
    values = dict(row)  # type: ignore[arg-type]
    provider = values["provider"]
    return AppSettingsResponse(
        **values,
        provider_configured=bool(
            settings.gemini_api_key if provider == "gemini" else settings.groq_api_key
        ),
    )


@router.get("", response_model=AppSettingsResponse)
def read_settings(settings: Settings = Depends(get_settings)) -> AppSettingsResponse:
    with connect(settings) as connection:
        row = connection.execute(
            "SELECT provider, gemini_model, groq_model, rag_top_k, theme "
            "FROM app_settings WHERE id = 1"
        ).fetchone()
    if row is None:
        raise RuntimeError("Application settings were not initialized")
    return _response(row, settings)


@router.put("", response_model=AppSettingsResponse)
def update_settings(
    payload: AppSettingsUpdate,
    settings: Settings = Depends(get_settings),
) -> AppSettingsResponse:
    with connect(settings) as connection:
        connection.execute(
            """
            UPDATE app_settings
            SET provider = ?, gemini_model = ?, groq_model = ?, rag_top_k = ?,
                theme = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (
                payload.provider,
                payload.gemini_model,
                payload.groq_model,
                payload.rag_top_k,
                payload.theme,
            ),
        )
        row = connection.execute(
            "SELECT provider, gemini_model, groq_model, rag_top_k, theme "
            "FROM app_settings WHERE id = 1"
        ).fetchone()
    return _response(row, settings)


# app/routes/sync_oportunidad.py
#
# Prueba piloto (Plan de Migración v1.1). Lo llama la web interna después
# de guardar una Oportunidad en la base local, para crearla en GHL.
#
# Recibe el Authorization: Bearer <token> del usuario logueado en la web
# interna (su propio access token de Supabase) y lo reenvía tal cual a
# Supabase/PostgREST vía oportunidad_sync_service — son las políticas RLS
# de integracion-ghl-ns las que deciden si ese usuario puede leer/editar
# esa oportunidad. Este servicio no valida permisos por su cuenta ni
# guarda una service_role key de Supabase.

import logging

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse

from app.services.oportunidad_sync_service import sync_oportunidad_a_ghl

logger = logging.getLogger("sync_oportunidad_route")

router = APIRouter()


@router.post("/admin/sync-oportunidad/{oportunidad_id}")
async def sync_oportunidad(oportunidad_id: str, authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Falta el header Authorization: Bearer <token de Supabase del usuario>",
        )

    user_token = authorization.split(" ", 1)[1].strip()

    resultado = sync_oportunidad_a_ghl(oportunidad_id, user_token)

    if not resultado["ok"]:
        raise HTTPException(status_code=resultado["status"], detail=resultado["detail"])

    return JSONResponse(content=resultado, status_code=resultado["status"])

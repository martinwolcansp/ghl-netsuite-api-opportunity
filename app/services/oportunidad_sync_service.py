# app/services/oportunidad_sync_service.py
#
# Prueba piloto (Plan de Migración v1.1): toma una Oportunidad ya cargada
# a mano en la base local de la web interna — junto a su Contacto, que ya
# existe en GHL de antes — y la crea en GHL si todavía no tiene
# ghl_opportunity_id.
#
# Diferencia a propósito con el flujo de producción (ghl_opportunity_service
# .sync_opportunity, usado por /webhook/opportunity): ese flujo busca en GHL
# por el custom field de NetSuite Opportunity ID antes de crear, para no
# duplicar si NetSuite reintenta el webhook. Acá, en esta primera etapa,
# la Oportunidad puede no tener ns_opportunity_id todavía (la recepción
# NS → creación queda para la segunda etapa de desarrollo), así que no hay
# nada confiable para buscar por ese lado. La idempotencia es local en
# cambio: si la fila ya tiene ghl_opportunity_id cargado, no se vuelve a
# crear.

import logging
import requests
from datetime import datetime, timezone

from app.clients.supabase_client import (
    get_oportunidad_con_contacto,
    actualizar_sync_oportunidad,
)
from app.clients.ghl_client import create_opportunity
from app.services.opportunity_mapper import (
    build_create_payload,
    map_unidad_comercial,
)
from app.core.config import (
    GHL_LOCATION_ID,
    PIPELINE_ID,
    PIPELINE_STAGE_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID,
)

logger = logging.getLogger("oportunidad_sync_service")


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def sync_oportunidad_a_ghl(oportunidad_id, user_token):
    try:
        row, _resp = get_oportunidad_con_contacto(oportunidad_id, user_token)
    except requests.exceptions.RequestException as e:
        # Supabase inalcanzable (caída, timeout, DNS, etc.). No hay forma de
        # persistir el estado "error" acá porque justamente no se puede
        # escribir en Supabase — se devuelve el error tal cual para que el
        # sitio lo muestre, sin romper con un 500 genérico.
        mensaje = f"No se pudo conectar con la base de datos: {e}"
        logger.error(mensaje)
        return {"ok": False, "status": 503, "detail": mensaje}

    if row is None:
        return {
            "ok": False,
            "status": 404,
            "detail": "Oportunidad no encontrada (o sin permiso para verla).",
        }

    contacto = row.get("contacto")
    if not contacto or not contacto.get("ghl_contact_id"):
        mensaje = "El contacto asociado no tiene ID de contacto GHL cargado."
        actualizar_sync_oportunidad(oportunidad_id, user_token, {
            "sync_estado": "error",
            "sync_mensaje": mensaje,
            "sync_actualizado_en": _now_iso(),
        })
        return {"ok": False, "status": 422, "detail": mensaje}

    if row.get("ghl_opportunity_id"):
        return {
            "ok": True,
            "status": 200,
            "detail": "Ya estaba sincronizada con GHL.",
            "ghl_opportunity_id": row["ghl_opportunity_id"],
        }

    customer_name = " ".join(
        parte for parte in [contacto.get("nombre"), contacto.get("apellido")] if parte
    ).strip()

    # unidad_comercial en la tabla ya es texto libre ("Hogar Seguro", etc).
    # class_ns (el código numérico de NetSuite) queda reservado para cuando
    # la recepción desde NS complete ese campo; si está, se prioriza para
    # reusar exactamente el mismo mapeo que ya usa el flujo de producción.
    unidad = row.get("unidad_comercial") or ""
    if row.get("class_ns") is not None:
        unidad = map_unidad_comercial(row["class_ns"])

    payload = build_create_payload(
        location_id=GHL_LOCATION_ID,
        pipeline_id=PIPELINE_ID,
        pipeline_stage_id=row.get("pipeline_stage_id") or PIPELINE_STAGE_ID,
        contact_id=contacto["ghl_contact_id"],
        customer_name=customer_name,
        netsuite_opportunity_id=row.get("ns_opportunity_id") or "",
        titulo_oportunidad=row.get("titulo") or "",
        unidad_comercial=unidad,
        custom_field_ns_id=CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID,
    )

    try:
        ghl_resp = create_opportunity(payload)
    except requests.exceptions.RequestException as e:
        # GHL inalcanzable, timeout, DNS caído, etc. — antes esto se iba sin
        # capturar y la oportunidad quedaba en "Pendiente" para siempre en
        # vez de "Error". Ahora sí queda registrado y con reintento posible.
        mensaje = f"No se pudo conectar con GHL: {e}"
        try:
            actualizar_sync_oportunidad(oportunidad_id, user_token, {
                "sync_estado": "error",
                "sync_mensaje": mensaje,
                "sync_actualizado_en": _now_iso(),
            })
        except requests.exceptions.RequestException:
            logger.error("Además de fallar GHL, no se pudo actualizar sync_estado en Supabase")
        return {"ok": False, "status": 503, "detail": mensaje}

    if ghl_resp.status_code not in (200, 201):
        mensaje = f"GHL respondió {ghl_resp.status_code}: {ghl_resp.text[:300]}"
        actualizar_sync_oportunidad(oportunidad_id, user_token, {
            "sync_estado": "error",
            "sync_mensaje": mensaje,
            "sync_actualizado_en": _now_iso(),
        })
        return {"ok": False, "status": 502, "detail": mensaje}

    ghl_id = None
    try:
        body = ghl_resp.json()
        ghl_id = (body.get("opportunity") or body).get("id")
    except Exception:
        logger.warning("No se pudo leer el id de la respuesta de GHL al crear la oportunidad")

    now = _now_iso()
    cambios = {
        "sync_estado": "sincronizado",
        "sync_mensaje": None,
        "sync_actualizado_en": now,
    }
    if ghl_id:
        cambios["ghl_opportunity_id"] = ghl_id
    if not row.get("fecha_creacion_ghl"):
        cambios["fecha_creacion_ghl"] = now

    actualizar_sync_oportunidad(oportunidad_id, user_token, cambios)

    return {
        "ok": True,
        "status": 201,
        "detail": "Oportunidad creada en GHL.",
        "ghl_opportunity_id": ghl_id,
    }

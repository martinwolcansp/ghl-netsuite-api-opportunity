import logging
import requests

from app.clients.ghl_client import update_opportunity, create_opportunity
from app.core.config import (
    GHL_API_KEY,
    GHL_LOCATION_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID,
    MODO_SIMULACION
)

logger = logging.getLogger("ghl_service")

GHL_BASE_URL = "https://services.leadconnectorhq.com"


# ===============================
# SEARCH OPPORTUNITY (ESTILO PRESUPUESTO)
# ===============================
def find_opportunity(contact_id, opportunity_id):

    logger.info("========== GHL OPPORTUNITY SEARCH ==========")
    logger.info(f"Contact ID: {contact_id}")
    logger.info(f"NS Opportunity ID: {opportunity_id}")

    resp = requests.get(
        f"{GHL_BASE_URL}/opportunities/search",
        headers={
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Accept": "application/json",
            "Version": "2021-07-28"
        },
        params={
            "location_id": GHL_LOCATION_ID,
            "contact_id": contact_id
        }
    )

    if resp.status_code not in (200, 201):
        logger.error(f"GHL search error: {resp.text}")
        return None

    opportunities = resp.json().get("opportunities", [])

    logger.info(f"📦 Opportunities found: {len(opportunities)}")

    for opp in opportunities:

        logger.info("--------------------------------------")
        logger.info(f"Checking Opportunity ID: {opp.get('id')}")
        logger.info(f"Name: {opp.get('name')}")

        for cf in opp.get("customFields", []):

            value = (
                cf.get("fieldValue")
                or cf.get("fieldValueString")
                or cf.get("value")
            )

            logger.info(f"CF {cf.get('id')} = {value}")

            if (
                cf.get("id") == CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
                and str(value) == str(opportunity_id)
            ):
                logger.info("🎯 MATCH FOUND BY NS ID")
                return opp

    logger.warning("❌ No matching opportunity found")
    return None


# ===============================
# PROPIETARIO RECHAZADO → REINTENTO SIN PROPIETARIO
# ===============================
# Si GHL rechaza el envío (4xx) y llevaba propietario (ID de usuario
# inexistente o mal cargado en NetSuite), se reintenta sin él para que la
# oportunidad se guarde igual. Devuelve (respuesta, info del propietario).
def _enviar_con_propietario(enviar, payload, representante):
    assigned_to = payload.get("assignedTo")

    if not assigned_to:
        return enviar(payload), {"estado": "sin_dato", "representante": representante}

    resp = enviar(payload)

    if 400 <= resp.status_code < 500:
        logger.warning(
            f"GHL rechazó el envío con propietario {assigned_to} ({representante}): "
            f"se reintenta sin propietario"
        )
        detalle = resp.text[:300]
        sin_propietario = {k: v for k, v in payload.items() if k != "assignedTo"}
        resp = enviar(sin_propietario)
        return resp, {
            "estado": "rechazado",
            "ghl_user_id": assigned_to,
            "representante": representante,
            "detalle": detalle
        }

    return resp, {"estado": "asignado", "ghl_user_id": assigned_to, "representante": representante}


# ===============================
# SYNC OPPORTUNITY (CREATE + UPDATE)
# ===============================
def sync_opportunity(
    contact_id,
    opportunity_id=None,
    netsuite_opportunity_id=None,
    create_payload=None,
    update_payload_builder=None,
    representante=None
):

    # ===============================
    # COMPATIBILIDAD DE NOMBRE
    # ===============================
    if opportunity_id is None:
        opportunity_id = netsuite_opportunity_id

    logger.info("========== OPPORTUNITY SYNC NS → GHL ==========")
    logger.info(f"NS Opportunity ID: {opportunity_id}")

    # ===============================
    # VALIDACIÓN
    # ===============================
    if not contact_id:
        logger.error("❌ Missing contact_id → aborting")
        return {"error": "missing_contact_id"}

    # ===============================
    # SEARCH
    # ===============================
    matching = find_opportunity(contact_id, opportunity_id)

    # ===============================
    # CREATE
    # ===============================
    if not matching:

        logger.warning("⚠️ Opportunity not found → creating")

        # ===============================
        # MODO SIMULACIÓN (servidor local)
        # ===============================
        # No crea en GHL: registra el alta exacta que habría hecho. Sólo
        # aplica a este flujo (webhook de NetSuite), no al sitio interno.
        if MODO_SIMULACION:
            logger.info(f"[SIMULACION] POST {GHL_BASE_URL}/opportunities/")
            logger.info(f"[SIMULACION] Payload: {create_payload}")
            return {
                "action": "created",
                "status": 201,
                "simulado": True,
                "payload": create_payload
            }

        resp, propietario = _enviar_con_propietario(
            create_opportunity, create_payload, representante
        )

        resultado = {
            "action": "created",
            "status": resp.status_code,
            "propietario": propietario
        }
        if resp.status_code not in (200, 201):
            resultado["ghl_error"] = resp.text[:1000]
        return resultado

    # ===============================
    # EXISTS → UPDATE (nombre, título y unidad comercial)
    # ===============================
    # Pasa al reenviar desde el botón "Enviar a GHL" de NetSuite. No cambia
    # etapa ni estado (ver build_update_payload).
    ghl_id = matching["id"]

    logger.info("========== EXISTING OPPORTUNITY ==========")
    logger.info(f"GHL ID: {ghl_id}")

    if not update_payload_builder:
        logger.info("⏭ Opportunity already exists → no update builder, no action taken")
        return {
            "action": "already_exists",
            "id": ghl_id
        }

    payload = update_payload_builder(matching)

    if MODO_SIMULACION:
        logger.info(f"[SIMULACION] PUT {GHL_BASE_URL}/opportunities/{ghl_id}")
        logger.info(f"[SIMULACION] Payload: {payload}")
        return {
            "action": "updated",
            "status": 200,
            "simulado": True,
            "id": ghl_id,
            "payload": payload
        }

    resp, propietario = _enviar_con_propietario(
        lambda p: update_opportunity(opportunity_id=ghl_id, payload=p),
        payload,
        representante
    )

    resultado = {
        "action": "updated",
        "status": resp.status_code,
        "id": ghl_id,
        "custom_fields_enviados": payload.get("customFields"),
        "propietario": propietario
    }
    if resp.status_code not in (200, 201):
        resultado["ghl_error"] = resp.text[:1000]
    return resultado


# ===============================
# UPDATE (DESHABILITADO - FUTURO)
# ===============================
# def update_flow(matching, update_payload_builder):
#
#     ghl_id = matching["id"]
#
#     logger.info("========== EXISTING OPPORTUNITY ==========")
#     logger.info(f"GHL ID: {ghl_id}")
#
#     payload = update_payload_builder(matching)
#
#     current_stage = matching.get("pipelineStageId")
#     current_status = matching.get("status")
#
#     if (
#         current_stage == payload.get("pipelineStageId")
#         and current_status == payload.get("status")
#     ):
#         logger.info("⏭ No changes (idempotent)")
#         return {"status": "already_updated"}
#
#     logger.info("========== FINAL UPDATE ==========")
#     logger.info(f"Stage: {current_stage} → {payload.get('pipelineStageId')}")
#     logger.info(f"Status: {current_status} → {payload.get('status')}")
#
#     resp = update_opportunity(
#         opportunity_id=ghl_id,
#         payload=payload
#     )
#
#     logger.info("========== GHL UPDATE RESPONSE ==========")
#     logger.info(f"STATUS: {resp.status_code}")
#     logger.info(f"BODY: {resp.text}")
#
#     return {"action": "updated"}


# backward compatibility
upsert_opportunity = sync_opportunity
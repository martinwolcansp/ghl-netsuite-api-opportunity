import hmac
import logging
import time

from fastapi import APIRouter, Request, HTTPException

from app.services.ghl_opportunity_service import sync_opportunity
from app.services.opportunity_mapper import (
    build_create_payload,
    build_update_payload,
    map_unidad_comercial
)

from app.core.config import (
    GHL_LOCATION_ID,
    PIPELINE_ID,
    PIPELINE_STAGE_ID,
    CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID,
    WEBHOOK_SECRET
)
from app import registro_eventos

router = APIRouter()

logger = logging.getLogger("opportunity_webhook")


def _resultado_de(result):
    """Traduce la respuesta del servicio al resultado del registro de eventos.
    Sólo para el registro: la respuesta a NetSuite no cambia."""
    if result.get("error"):
        return "error", str(result["error"])
    if result.get("simulado"):
        return "simulado", None
    if result.get("action") == "already_exists":
        return "already_exists", None
    if result.get("action") == "created":
        if result.get("status") in (200, 201):
            return "created", None
        # Hallazgo 2: el servicio responde 200 aunque GHL rechace el alta.
        # La respuesta no se toca, pero el registro muestra el error real.
        return "error", f"GHL rechazó el alta (HTTP {result.get('status')})"
    if result.get("action") == "updated":
        if result.get("status") in (200, 201):
            return "updated", None
        return "error", f"GHL rechazó la actualización (HTTP {result.get('status')})"
    return "error", "Respuesta no reconocida"


@router.post("/webhook/opportunity")
async def opportunity_webhook(request: Request):

    inicio = time.monotonic()
    payload = None

    # ===============================
    # REGISTRO DE EVENTOS (pestaña En vivo)
    # ===============================
    # No cambia la respuesta: se escribe en segundo plano.
    def registrar(resultado, respuesta=None, detalle=None):
        referencia = payload.get("netsuite_opportunity_id") if isinstance(payload, dict) else None
        registro_eventos.registrar(
            etapa="oportunidad",
            origen="netsuite",
            resultado=resultado,
            referencia_id=referencia,
            detalle=detalle,
            payload=payload,
            respuesta=respuesta,
            duracion_ms=int((time.monotonic() - inicio) * 1000),
        )

    # ===============================
    # SECRETO COMPARTIDO (servidor local)
    # ===============================
    # Sólo se exige si WEBHOOK_SECRET tiene valor. Acepta el header
    # X-Integration-Secret o el parámetro ?token=.
    if WEBHOOK_SECRET:
        recibido = (
            request.headers.get("X-Integration-Secret")
            or request.query_params.get("token")
            or ""
        )
        if not hmac.compare_digest(recibido, WEBHOOK_SECRET):
            logger.warning("Webhook rechazado: secreto ausente o inválido")
            registrar("rechazado", detalle="Secreto ausente o inválido")
            raise HTTPException(status_code=401, detail="unauthorized")

    try:
        payload = await request.json()

        contact_id = payload.get("ghl_contact_id")
        ns_id = payload.get("netsuite_opportunity_id")

        if not contact_id or not ns_id:
            registrar("error", {"detail": "Missing data"},
                      "Faltan ghl_contact_id o netsuite_opportunity_id")
            raise HTTPException(status_code=400, detail="Missing data")

        unidad = map_unidad_comercial(payload.get("unidad_comercial"))

        create_payload = build_create_payload(
            location_id=GHL_LOCATION_ID,
            pipeline_id=PIPELINE_ID,
            pipeline_stage_id=PIPELINE_STAGE_ID,
            contact_id=contact_id,
            customer_name=payload.get("netsuite_customer_name"),
            netsuite_opportunity_id=ns_id,
            titulo_oportunidad=payload.get("titulo_oportunidad"),
            unidad_comercial=unidad,
            custom_field_ns_id=CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID
        )

        result = sync_opportunity(
            contact_id=contact_id,
            opportunity_id=ns_id,
            create_payload=create_payload,
            update_payload_builder=lambda existing: build_update_payload(
                existing,
                payload.get("netsuite_customer_name"),
                payload.get("titulo_oportunidad"),
                unidad
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        registrar("error", {"error": str(e)}, str(e))
        raise

    resultado, detalle = _resultado_de(result)
    registrar(resultado, result, detalle)

    return result

# app/services/opportunity_mapper.py

import logging

from app.clients.ghl_client import get_opportunity_custom_fields

logger = logging.getLogger("opportunity_mapper")


def _campo(clave, valor):
    """Arma un campo personalizado para GHL. Usa el ID interno del campo
    (buscado por su clave en la cuenta); si no se encuentra, envía la clave
    como último recurso y lo deja en el log."""
    campos = get_opportunity_custom_fields()
    info = campos.get(clave)

    if not info or not info.get("id"):
        logger.warning(
            f"Campo personalizado '{clave}' no encontrado en GHL: se envía por clave"
        )
        return {"key": clave, "field_value": valor}

    opciones = info.get("opciones") or []
    if opciones and valor not in opciones:
        logger.warning(
            f"El valor '{valor}' no es una opción del campo '{clave}' "
            f"({info.get('tipo')}). Opciones: {opciones}"
        )

    return {"id": info["id"], "field_value": valor}

def map_unidad_comercial(valor):
    # Campo "Unidad comercial" de la oportunidad en NetSuite
    # (custbody_mw_sp_unidad_comercial). Hoy sólo se carga en
    # alarmas nuevas. No confundir con la unidad de negocio (class).
    mapping = {
        "1": "Hogar",
        "2": "Comercio",
        "3": "Obra",
        "8": "Gubernamental"
    }
    return mapping.get(str(valor), "Otro")


# ===============================
# BUILD NAME (UNIFICADO)
# ===============================
def build_opportunity_name(customer_name, titulo):
    name = customer_name or ""

    if titulo:
        name = f"{name} - {titulo}"

    return name


def build_create_payload(
    location_id,
    pipeline_id,
    pipeline_stage_id,
    contact_id,
    customer_name,
    netsuite_opportunity_id,
    titulo_oportunidad,
    unidad_comercial,
    custom_field_ns_id
):
    name = build_opportunity_name(customer_name, titulo_oportunidad)

    return {
        "locationId": location_id,
        "pipelineId": pipeline_id,
        "pipelineStageId": pipeline_stage_id,
        "contactId": contact_id,
        "name": name,
        "status": "open",
        # Los campos personalizados se envían por su ID interno de GHL.
        # "titulo_oportunidad" y "unidad_comercial_ns" son claves: _campo()
        # busca el ID correspondiente en la cuenta. Antes la clave iba en
        # "id" y GHL los ignoraba sin dar error.
        "customFields": [
            {
                "id": custom_field_ns_id,
                "field_value": str(netsuite_opportunity_id)
            },
            _campo("titulo_oportunidad", titulo_oportunidad),
            _campo("unidad_comercial_ns", unidad_comercial)
        ]
    }


def build_update_payload(
    existing,
    customer_name,
    titulo_oportunidad,
    unidad_comercial
):
    # Actualiza sólo nombre y datos informativos. NO toca la etapa ni el
    # estado: los maneja la integración de presupuestos, y reenviar la
    # oportunidad no debe devolverla a la etapa inicial.
    name = build_opportunity_name(customer_name, titulo_oportunidad)

    return {
        "name": name,
        "customFields": [
            _campo("titulo_oportunidad", titulo_oportunidad),
            _campo("unidad_comercial_ns", unidad_comercial)
        ]
    }
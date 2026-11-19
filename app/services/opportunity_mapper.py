# app/services/opportunity_mapper.py

import logging
from datetime import datetime

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

# Formatos en que puede llegar la fecha desde NetSuite (getText de trandate
# usa el formato de la cuenta: en SP es día/mes/año).
_FORMATOS_FECHA_NS = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y")


def _campo_fecha(clave, texto):
    """Campo personalizado de fecha. Si el campo de GHL es de tipo fecha
    se envía AAAA-MM-DD; si es de texto, DD/MM/AAAA. Si la fecha no se puede
    interpretar se envía tal como llegó y queda en el log."""
    texto = (texto or "").strip()
    if not texto:
        return None

    fecha = None
    for formato in _FORMATOS_FECHA_NS:
        try:
            fecha = datetime.strptime(texto, formato).date()
            break
        except ValueError:
            continue

    if not fecha:
        logger.warning(f"Fecha '{texto}' no reconocida para '{clave}': se envía sin convertir")
        return _campo(clave, texto)

    tipo = (get_opportunity_custom_fields().get(clave) or {}).get("tipo")
    valor = fecha.isoformat() if tipo == "DATE" else fecha.strftime("%d/%m/%Y")
    return _campo(clave, valor)


def _campos_documento(numero_oportunidad, fecha_oportunidad):
    """Número y fecha de la oportunidad de NetSuite. Sólo se envían los que
    tienen valor (el alta desde el sitio interno no los trae)."""
    campos = []
    if numero_oportunidad:
        campos.append(_campo("netsuite_opportunity_opt", str(numero_oportunidad)))
    fecha = _campo_fecha("netsuite_opportunity_date", fecha_oportunidad)
    if fecha:
        campos.append(fecha)
    return campos


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
    custom_field_ns_id,
    numero_oportunidad=None,
    fecha_oportunidad=None
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
        ] + _campos_documento(numero_oportunidad, fecha_oportunidad)
    }


def build_update_payload(
    existing,
    customer_name,
    titulo_oportunidad,
    unidad_comercial,
    numero_oportunidad=None,
    fecha_oportunidad=None
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
        ] + _campos_documento(numero_oportunidad, fecha_oportunidad)
    }
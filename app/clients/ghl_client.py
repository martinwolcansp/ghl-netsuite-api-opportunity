import requests
import logging
from app.core.config import GHL_API_KEY

logger = logging.getLogger("ghl_client")

GHL_BASE_URL = "https://services.leadconnectorhq.com"


# ===============================
# COMMON HEADERS
# ===============================
def _headers():
    return {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }


# ===============================
# CAMPOS PERSONALIZADOS DE OPORTUNIDAD (clave -> ID)
# ===============================
# GHL identifica los campos personalizados por su ID interno. Se leen una
# vez de la cuenta y se guardan en memoria; si la lectura falla no se guarda
# nada y se reintenta en el próximo envío.
_cache_campos = {}


def get_opportunity_custom_fields():
    from app.core.config import GHL_LOCATION_ID

    if _cache_campos:
        return _cache_campos

    try:
        resp = requests.get(
            f"{GHL_BASE_URL}/locations/{GHL_LOCATION_ID}/customFields",
            headers=_headers(),
            params={"model": "opportunity"},
            timeout=15,
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"No se pudieron leer los campos personalizados de GHL: {e}")
        return {}

    if resp.status_code != 200:
        logger.error(
            f"No se pudieron leer los campos personalizados de GHL: "
            f"HTTP {resp.status_code} - {resp.text[:500]}"
        )
        return {}

    for cf in resp.json().get("customFields", []):
        clave = (cf.get("fieldKey") or "").replace("opportunity.", "", 1)
        if clave:
            _cache_campos[clave] = {
                "id": cf.get("id"),
                "nombre": cf.get("name"),
                "tipo": cf.get("dataType"),
                "opciones": cf.get("picklistOptions") or [],
            }

    logger.info(f"Campos personalizados de oportunidad en GHL: {_cache_campos}")
    return _cache_campos


# ===============================
# CREATE OPPORTUNITY
# ===============================
def create_opportunity(payload):

    logger.info("========== GHL CREATE REQUEST ==========")
    logger.info(f"Payload: {payload}")

    resp = requests.post(
        f"{GHL_BASE_URL}/opportunities/",
        headers=_headers(),
        json=payload,
        timeout=15,
    )

    logger.info("========== GHL CREATE RESPONSE ==========")
    logger.info(f"STATUS: {resp.status_code}")
    logger.info(f"BODY: {resp.text}")

    if resp.status_code in (200, 201):
        logger.info("✅ SUCCESS create opportunity")
    else:
        logger.error("❌ ERROR creating opportunity")

    return resp


# ===============================
# UPDATE OPPORTUNITY (DESHABILITADO EN SERVICE)
# ===============================
def update_opportunity(opportunity_id, payload):

    logger.info("========== GHL UPDATE REQUEST ==========")
    logger.info(f"Opportunity ID: {opportunity_id}")
    logger.info(f"Payload: {payload}")

    resp = requests.put(
        f"{GHL_BASE_URL}/opportunities/{opportunity_id}",
        headers=_headers(),
        json=payload,
        timeout=15,
    )

    logger.info("========== GHL UPDATE RESPONSE ==========")
    logger.info(f"STATUS: {resp.status_code}")
    logger.info(f"BODY: {resp.text}")

    if resp.status_code in (200, 201):
        logger.info(f"✅ SUCCESS update opp {opportunity_id}")
    else:
        logger.error(f"❌ ERROR updating opp {opportunity_id}")

    return resp
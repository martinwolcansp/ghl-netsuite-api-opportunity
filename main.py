import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# =========================
# ENV
# =========================
GHL_API_KEY = os.getenv("GHL_API_KEY")
LOCATION_ID = os.getenv("LOCATION_ID")
PIPELINE_ID = os.getenv("PIPELINE_ID")
PIPELINE_STAGE_ID = os.getenv("PIPELINE_STAGE_ID")
NETSUITE_OPP_CF_ID = os.getenv("NETSUITE_OPP_CF_ID")

GHL_BASE_URL = "https://services.leadconnectorhq.com"

# =========================
# MAP UNIDAD COMERCIAL
# =========================
UNIDAD_COMERCIAL_MAP = {
    "1": "Hogar Seguro",
    "2": "Comercio Seguro",
    "3": "Obra Segura"
}

# =========================
# UTILS
# =========================
def env_check():
    return {
        "GHL_API_KEY": bool(GHL_API_KEY),
        "LOCATION_ID": LOCATION_ID,
        "PIPELINE_ID": PIPELINE_ID,
        "PIPELINE_STAGE_ID": PIPELINE_STAGE_ID,
        "NETSUITE_OPP_CF_ID": NETSUITE_OPP_CF_ID
    }

def ghl_headers():
    return {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Version": "2021-07-28"
    }

# =========================
# WEBHOOK
# =========================
@app.post("/webhook/opportunity")
async def webhook_opportunity(request: Request):

    payload = await request.json()

    print("🔥 Webhook recibido desde NetSuite")
    print(payload)

    print("🧪 ENV CHECK", env_check())

    # -------------------------
    # Validaciones mínimas
    # -------------------------
    required_envs = [
        GHL_API_KEY,
        LOCATION_ID,
        PIPELINE_ID,
        PIPELINE_STAGE_ID,
        NETSUITE_OPP_CF_ID
    ]

    if not all(required_envs):
        print("❌ Variables de entorno incompletas")
        return {"status": "error", "message": "ENV incompleto"}

    ghl_contact_id = payload.get("ghl_contact_id")
    netsuite_opportunity_id = payload.get("netsuite_opportunity_id")
    customer_name = payload.get("netsuite_customer_name")
    titulo_oportunidad = payload.get("titulo_oportunidad")
    unidad_comercial_ns = payload.get("unidad_comercial")

    # -------------------------
    # Traducción unidad comercial
    # -------------------------
    unidad_comercial = None
    if unidad_comercial_ns:
        unidad_comercial = UNIDAD_COMERCIAL_MAP.get(str(unidad_comercial_ns))

    print("🏷 Unidad comercial traducida:", unidad_comercial)

    if not ghl_contact_id:
        print("❌ ghl_contact_id faltante")
        return {"status": "error", "message": "ghl_contact_id requerido"}

    if not customer_name:
        print("❌ netsuite_customer_name faltante")
        return {"status": "error", "message": "netsuite_customer_name requerido"}

    # -------------------------
    # Payload GHL
    # -------------------------
    ghl_payload = {
        "locationId": LOCATION_ID,
        "pipelineId": PIPELINE_ID,
        "pipelineStageId": PIPELINE_STAGE_ID,
        "contactId": ghl_contact_id,
        "name": customer_name,
        "status": "open",
        "customFields": [
            {
                "id": NETSUITE_OPP_CF_ID,
                "field_value": str(netsuite_opportunity_id)
            },
            {
                "id": "titulo_oportunidad",
                "field_value": titulo_oportunidad
            },
            {
                "id": "unidad_comercial_ns",
                "field_value": unidad_comercial
            }
        ]
    }

    print("🚀 Creando Opportunity en GHL")
    print(ghl_payload)

    response = requests.post(
        f"{GHL_BASE_URL}/opportunities/",
        headers=ghl_headers(),
        json=ghl_payload,
        timeout=30
    )

    print("📨 Respuesta GHL:", response.status_code)
    print(response.text)

    if response.status_code >= 400:
        return {
            "status": "error",
            "ghl_status": response.status_code,
            "ghl_response": response.text
        }

    return {
        "status": "ok",
        "ghl_response": response.json()
    }
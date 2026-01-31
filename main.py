import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# =========================
# ENV
# =========================
GHL_TOKEN = os.getenv("GHL_TOKEN")
LOCATION_ID = os.getenv("LOCATION_ID")
PIPELINE_ID = os.getenv("PIPELINE_ID")
PIPELINE_STAGE_ID = os.getenv("STAGE_ID")  # stage real
NETSUITE_OPP_CF_ID = os.getenv("NETSUITE_OPP_CF_ID")  # custom field ID en GHL

GHL_BASE_URL = "https://services.leadconnectorhq.com"

# =========================
# UTILS
# =========================
def env_check():
    return {
        "LOCATION_ID": LOCATION_ID,
        "PIPELINE_ID": PIPELINE_ID,
        "PIPELINE_STAGE_ID": PIPELINE_STAGE_ID,
        "NETSUITE_OPP_CF_ID": NETSUITE_OPP_CF_ID
    }

def ghl_headers():
    return {
        "Authorization": f"Bearer {GHL_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
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
        GHL_TOKEN,
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
    netsuite_title = payload.get("netsuite_title")

    if not ghl_contact_id:
        print("❌ ghl_contact_id faltante")
        return {"status": "error", "message": "ghl_contact_id requerido"}

    # -------------------------
    # Payload correcto GHL
    # -------------------------
    ghl_payload = {
        "locationId": LOCATION_ID,
        "pipelineId": PIPELINE_ID,
        "pipelineStageId": PIPELINE_STAGE_ID,
        "contactId": ghl_contact_id,
        "name": netsuite_title or f"Opportunity {netsuite_opportunity_id}",
        "status": "open",
        "customFields": [
            {
                "id": NETSUITE_OPP_CF_ID,
                "field_value": str(netsuite_opportunity_id)
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
            "ghl_response": response.json()
        }

    return {
        "status": "ok",
        "ghl_response": response.json()
    }

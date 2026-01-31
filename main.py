from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

GHL_API_KEY = os.getenv("GHL_API_KEY")
LOCATION_ID = os.getenv("GHL_LOCATION_ID")
PIPELINE_ID = os.getenv("GHL_PIPELINE_ID")
STAGE_ID = os.getenv("GHL_STAGE_ID")

GHL_OPPORTUNITY_URL = "https://services.leadconnectorhq.com/opportunities/"

@app.post("/webhook/opportunity")
async def receive_opportunity(request: Request):
    payload = await request.json()

    print("🔥 Webhook recibido desde NetSuite")
    print(payload)

    print("🧪 ENV CHECK", {
        "LOCATION_ID": LOCATION_ID,
        "PIPELINE_ID": PIPELINE_ID,
        "STAGE_ID": STAGE_ID
    })

    ghl_payload = {
        "contactId": payload.get("ghl_contact_id"),
        "name": payload.get("netsuite_title"),
        "pipelineId": PIPELINE_ID,
        "stageId": STAGE_ID,
        "status": "open",
        "externalId": str(payload.get("netsuite_opportunity_id"))
    }

    print("🚀 Creando Opportunity en GHL")
    print(ghl_payload)

    response = requests.post(
        GHL_OPPORTUNITY_URL,
        headers={
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Version": "2021-07-28",
            "Content-Type": "application/json",
            "Location-Id": LOCATION_ID     # HEADER
        },
        params={
            "locationId": LOCATION_ID     # QUERY PARAM (🔥 CLAVE)
        },
        json=ghl_payload,
        timeout=15
    )

    print("📨 Respuesta GHL:", response.status_code)
    print(response.text)

    if response.status_code not in (200, 201):
        return {
            "status": "error",
            "ghl_status": response.status_code,
            "ghl_response": response.text
        }

    ghl_response = response.json()

    return {
        "status": "ok",
        "ghl_opportunity_id": ghl_response.get("id")
    }

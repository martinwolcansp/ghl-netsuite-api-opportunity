from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/opportunity")
async def receive_opportunity(request: Request):
    payload = await request.json()
    print("🔥 Webhook recibido desde NetSuite")
    print(payload)
    return {"status": "ok"}

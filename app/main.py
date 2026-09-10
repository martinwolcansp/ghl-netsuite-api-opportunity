# app/main.py

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ===============================
# LOGGING CONFIG (IMPORTANTE EN RENDER)
# ===============================
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)

logger = logging.getLogger("app_main")

logger.info("========== APP STARTING ==========")
logger.info(f"Python version: {sys.version}")
logger.info(f"Sys path: {sys.path}")


# ===============================
# FASTAPI APP
# ===============================
app = FastAPI()


# ===============================
# CORS (prueba piloto: la web interna llama a /admin/sync-oportunidad
# desde el navegador). ALLOWED_ORIGINS se configura por variable de
# entorno; si queda vacía, se permite cualquier origen (ver
# app/core/config.py) -- restringir apenas la web interna tenga un
# dominio de producción fijo.
# ===============================
from app.core.config import ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===============================
# HEALTH CHECK (RENDER FRIENDLY)
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}


# ===============================
# IMPORT ROUTERS (CON CONTROL DE ERROR)
# ===============================
try:
    from app.webhooks.opportunity_webhook import router as opportunity_router
    app.include_router(opportunity_router)

    from app.routes.sync_oportunidad import router as sync_oportunidad_router
    app.include_router(sync_oportunidad_router)

    logger.info("✅ Routers loaded successfully (opportunity webhook + sync-oportunidad)")

except Exception as e:
    logger.error("❌ ERROR LOADING ROUTERS")
    logger.error(str(e))
    raise e
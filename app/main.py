# app/main.py

import logging
import sys

from fastapi import FastAPI

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

    logger.info("✅ Opportunity router loaded successfully")

except Exception as e:
    logger.error("❌ ERROR LOADING ROUTERS")
    logger.error(str(e))
    raise e
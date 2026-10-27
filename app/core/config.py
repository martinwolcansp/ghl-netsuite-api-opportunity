# app/core/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# GHL CORE
# =========================
GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("LOCATION_ID")

PIPELINE_ID = os.getenv("PIPELINE_ID")
PIPELINE_STAGE_ID = os.getenv("PIPELINE_STAGE_ID")

# =========================
# CUSTOM FIELDS
# =========================
CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID = os.getenv("CUSTOM_FIELD_NETSUITE_OPPORTUNITY_ID")

# =========================
# SUPABASE (prueba piloto — sincronización Oportunidad → GHL)
# =========================
# Se usa la anon key + el access token del usuario logueado en la web
# interna (reenviado en el Authorization header), NUNCA una service_role
# key acá: la autorización real la dan las políticas RLS de
# integracion-ghl-ns sobre las tablas contacto/oportunidad.
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# =========================
# CORS (para que la web interna pueda llamar a este servicio desde el navegador)
# =========================
# Lista separada por comas, ej: "https://interna.spseguridad.com.ar,https://otra.com"
# Si queda vacía, se permite cualquier origen (útil mientras la web interna
# todavía no tiene un dominio de producción fijo) — restringir apenas se
# tenga el dominio definitivo.
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

# =========================
# MIGRACIÓN AL SERVIDOR LOCAL (Parte II)
# =========================
# Interruptores para la réplica de la Etapa 2. Apagados por defecto: sin
# estas variables el webhook se comporta igual que en Render.
# Afectan SÓLO a /webhook/opportunity (el que llama NetSuite). El endpoint
# del sitio interno (/admin/sync-oportunidad) no los usa y sigue creando
# oportunidades reales en GHL.

# MODO_SIMULACION=true -> el webhook hace la búsqueda real en GHL pero no
# crea la oportunidad: registra en el log, con el prefijo [SIMULACION], el
# alta exacta que habría hecho.
MODO_SIMULACION = os.getenv("MODO_SIMULACION", "false").strip().lower() in (
    "true", "1", "si", "sí", "yes"
)

# WEBHOOK_SECRET con valor -> /webhook/opportunity exige el header
# X-Integration-Secret (o el parámetro ?token=) y rechaza con 401 lo que no
# lo traiga. Vacío -> no exige nada.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()

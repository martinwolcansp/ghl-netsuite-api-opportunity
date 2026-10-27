# registro_eventos.py — Registro de eventos de la integración en Supabase
# (tablas integration_events e integracion_estado, migración 41 de
# web_interna_sp). De ahí se alimenta la pestaña "En vivo" de la sección
# Integración NetSuite ↔ GHL.
#
# Es el mismo archivo en los tres servicios de la integración. Lee su
# configuración de variables de entorno:
#   REGISTRO_EVENTOS_ACTIVO   true para registrar. Por defecto false: no hace nada.
#   SUPABASE_URL              http://supabase-kong:8000 (red interna de Docker)
#   SUPABASE_ANON_KEY         anon key pública del sitio
#   INTEGRACION_BOT_EMAIL     usuario técnico de Supabase con permiso
#   INTEGRACION_BOT_PASSWORD  'editar' en integracion-ghl-ns
#
# La escritura se hace en un hilo aparte: nunca demora ni corta la
# respuesta del servicio. Si Supabase falla, queda una advertencia en el
# log y la integración sigue igual.

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger("registro_eventos")

ACTIVO = os.getenv("REGISTRO_EVENTOS_ACTIVO", "false").strip().lower() in (
    "true", "1", "si", "sí", "yes"
)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
BOT_EMAIL = os.getenv("INTEGRACION_BOT_EMAIL", "").strip()
BOT_PASSWORD = os.getenv("INTEGRACION_BOT_PASSWORD", "")

TIMEOUT = 8
MAX_TEXTO = 2000

_lock = threading.Lock()
_sesion = {"token": None, "vence": 0.0}


def configurado():
    return bool(ACTIVO and SUPABASE_URL and SUPABASE_ANON_KEY and BOT_EMAIL and BOT_PASSWORD)


def descripcion():
    """Texto para el log de arranque."""
    if not ACTIVO:
        return "apagado"
    faltan = [n for n, v in (
        ("SUPABASE_URL", SUPABASE_URL),
        ("SUPABASE_ANON_KEY", SUPABASE_ANON_KEY),
        ("INTEGRACION_BOT_EMAIL", BOT_EMAIL),
        ("INTEGRACION_BOT_PASSWORD", BOT_PASSWORD),
    ) if not v]
    return f"activo ({BOT_EMAIL})" if not faltan else f"activo pero falta configurar: {', '.join(faltan)}"


# ---------- sesión del usuario técnico ----------

def _token():
    with _lock:
        if _sesion["token"] and time.time() < _sesion["vence"]:
            return _sesion["token"]
        resp = requests.post(
            f"{SUPABASE_URL}/auth/v1/token",
            params={"grant_type": "password"},
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            json={"email": BOT_EMAIL, "password": BOT_PASSWORD},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"login del usuario técnico: HTTP {resp.status_code} {resp.text[:200]}")
        datos = resp.json()
        _sesion["token"] = datos["access_token"]
        _sesion["vence"] = time.time() + int(datos.get("expires_in", 3600)) - 120
        return _sesion["token"]


def _post(ruta, fila, prefer):
    for intento in (1, 2):
        token = _token()
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/{ruta}",
            headers={
                "apikey": SUPABASE_ANON_KEY,
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Prefer": prefer,
            },
            json=fila,
            timeout=TIMEOUT,
        )
        if resp.status_code == 401 and intento == 1:
            # Token vencido o revocado: se pide uno nuevo y se reintenta una vez.
            with _lock:
                _sesion["token"] = None
            continue
        if resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"HTTP {resp.status_code} {resp.text[:300]}")
        return


def _json_seguro(valor):
    if valor is None:
        return None
    try:
        json.dumps(valor)
        return valor
    except (TypeError, ValueError):
        return {"texto": str(valor)[:MAX_TEXTO]}


def _en_segundo_plano(funcion, *args):
    threading.Thread(target=funcion, args=args, daemon=True).start()


# ---------- eventos ----------

def _escribir_evento(fila):
    try:
        _post("integration_events", fila, "return=minimal")
    except Exception as e:  # noqa: BLE001 — nunca debe afectar a la integración
        logger.warning(f"No se pudo registrar el evento en Supabase: {e}")


def registrar(etapa, origen, resultado, referencia_id=None, detalle=None,
              payload=None, respuesta=None, duracion_ms=None):
    """Registra un evento (sin esperar). etapa: lead | oportunidad | presupuesto | sistema.
    origen: ghl | netsuite | local | servicio."""
    if not configurado():
        return
    fila = {
        "etapa": etapa,
        "origen": origen,
        "resultado": resultado,
        "referencia_id": str(referencia_id) if referencia_id not in (None, "") else None,
        "detalle": str(detalle)[:MAX_TEXTO] if detalle else None,
        "payload": _json_seguro(payload),
        "respuesta": _json_seguro(respuesta),
        "duracion_ms": duracion_ms,
    }
    _en_segundo_plano(_escribir_evento, fila)


# ---------- estado de la integración ----------

def _escribir_estado(fila):
    try:
        _post("integracion_estado?on_conflict=clave", fila,
              "resolution=merge-duplicates,return=minimal")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"No se pudo guardar el estado '{fila.get('clave')}' en Supabase: {e}")


def guardar_estado(clave, valor):
    """Guarda (o reemplaza) un valor de estado, sin esperar."""
    if not configurado():
        return
    fila = {
        "clave": clave,
        "valor": _json_seguro(valor),
        "actualizado_en": datetime.now(timezone.utc).isoformat(),
    }
    _en_segundo_plano(_escribir_estado, fila)

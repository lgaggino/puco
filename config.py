#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py – Configuración central para la aplicación Dash de Análisis de Padrones.
Contiene rutas, parámetros y el manager de long callbacks.
"""

from pathlib import Path
import diskcache as dc

# ─────────── RUTAS Y DIRECTORIOS ───────────
BASE_DIR    = Path(__file__).parent.resolve()
PADRON_DIR  = BASE_DIR / "padrones"
REF_DIR     = BASE_DIR / "referencias"
CACHE_DIR   = BASE_DIR / ".cache"

# Asegurarse de que existan
PADRON_DIR.mkdir(exist_ok=True)
REF_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# ─────────── PARÁMETROS DE CACHE Y BLOQUES ───────────
CHUNK_SIZE = 50_000           # filas por chunk en la lectura por streaming
CACHE_TTL  = 3 * 3600         # segundos de vida de la cache
APP_TITLE  = "Análisis de Padrones"

# ─────────── LONG CALLBACK MANAGER ───────────
# Se usa diskcache para almacenar resultados de callbacks largos
LONG_CACHE_DIR = CACHE_DIR / "long"
LONG_CACHE_DIR.mkdir(exist_ok=True)
_dc_cache = dc.Cache(str(LONG_CACHE_DIR))

try:
    # Dash ≥ 2.12
    from dash.long_callback import DiskcacheLongCallbackManager
except ImportError:
    # Fallback para versiones anteriores o dash-extensions
    from dash_extensions.enrich import DiskcacheLongCallbackManager  # type: ignore

LONGCALLBACK_MANAGER = DiskcacheLongCallbackManager(_dc_cache)
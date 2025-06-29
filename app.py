# app.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py – Punto de ensamblado de la aplicación Dash.
Crea la instancia, carga el layout y registra los callbacks.
"""

from dash import Dash
from app.config import APP_TITLE, LONGCALLBACK_MANAGER
from app.layout import layout
from app.callbacks import register_callbacks

# Crear la app y asignar layout + callbacks
app = Dash(
    __name__,
    title=APP_TITLE,
    long_callback_manager=LONGCALLBACK_MANAGER
)
app.layout = layout

register_callbacks(app)

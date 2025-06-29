#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run.py – Arranque de la app en modo producción/desarrollo,
con auto‐open del navegador.
"""

import threading
import webbrowser
import os
from app.app import app

if __name__ == "__main__":
    # Solo el proceso principal abre el navegador
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:8050/")).start()

    # Levantar servidor Dash
    app.run_server(port=8050, debug=True, use_reloader=False)

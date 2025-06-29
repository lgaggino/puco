# layout.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
layout.py – Define el layout de la aplicación y exporta COLS_EMP.
"""

import os
from pathlib import Path
from dash import html, dcc
from app.config import APP_TITLE, PADRON_DIR

# ────────────────────── columnas EMP ──────────────────────
COLS_EMP = [
    "sin_uso","codigo_emp","cuil_titular","codigo_parentesco","cuil_beneficiario",
    "tipo_documento","numero_documento","nombre_apellido","sexo","fecha_nacimiento",
    "nacionalidad","calle","puerta","piso","departamento","localidad","codigo_postal",
    "id_provincia","fijo","celular","mail","discapacidad","preexistente",
    "nombre_preexistente","afiliado","tipo_plan","codigo_afiliacion","ahesion",
    "corporativo","cuit_empleador","rnos","copago","valor","fecha_alta_entidad",
    "fecha_alta_plan","fecha_actualizacion","movimiento","sin_uso_1","sin_uso_2",
    "sin_uso_3","periodo",
]

layout = html.Div([
    html.H2(APP_TITLE), html.Hr(),

    dcc.RadioItems(
        id="padron",
        options=[
            {"label": "Entidades de Medicina Prepaga",    "value": "EMP"},
            {"label": "Obras Sociales Nacionales",        "value": "OSN"},
        ],
        value="EMP",
        labelStyle={"display": "inline-block", "margin-right": "18px"}
    ),
    html.Br(),

    dcc.Dropdown(
        id="archivos",
        options=[
            {"label": fn, "value": fn}
            for fn in sorted(os.listdir(PADRON_DIR))
            if fn.endswith(".txt")
        ],
        multi=True,
        placeholder="Seleccioná archivos"
    ),
    html.Br(),

    html.Button("Unificar", id="btn-unif"),
    html.Button("Analizar",  id="btn-anal", disabled=True),
    html.Button("Descargar", id="btn-dl",   disabled=True),
    dcc.Download(id="dl"),
    html.Br(),

    html.Div(id="out-resumen"), html.Br(),
    html.Div(id="panel"),

    # Stores para rutas y resultados
    dcc.Store(id="st-unif"),
    dcc.Store(id="st-sum"),
    dcc.Store(id="csv-m1"),
    dcc.Store(id="csv-dup"),
    dcc.Store(id="csv-err"),
])

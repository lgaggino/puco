#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
callbacks.py – Registra en la app todos los callbacks (unificación, análisis y descarga).
"""

import os
import time
import tempfile
import shutil
import zipfile
import io
import datetime
import re
from pathlib import Path
from collections import defaultdict, Counter

from dash import Input, Output, State, dash_table, dcc, html
from dash.exceptions import PreventUpdate

from app.config import PADRON_DIR, CACHE_DIR
from app.data_utils import leer_chunks, append_csv, sample_df, load_references, thousand
from app.layout import COLS_EMP

def register_callbacks(app):

    @app.callback(
        Output("btn-anal", "disabled"),
        Input("st-unif", "data"),
        Input("archivos", "value"),
    )
    def toggle_anal(unif, files):
        return not (unif or files)

    @app.callback(
        Output("btn-dl", "disabled"),
        Input("out-resumen", "children"),
    )
    def toggle_dl(res):
        return not bool(res)

    @app.callback(
        Output("st-unif",     "data"),
        Output("archivos",    "options"),
        Output("out-resumen", "children"),
        Output("panel",       "children"),
        Input("btn-unif",     "n_clicks"),
        State("archivos",     "value"),
        State("padron",       "value"),
        prevent_initial_call=True,
    )
    def unification(n_clicks, files, tp):
        if not files:
            raise PreventUpdate

        if tp == "EMP":
            cols = COLS_EMP
        else:
            df_ref, tablas = load_references(tp)
            cols = df_ref["campo"].tolist()

        outp = PADRON_DIR / f"unif_{int(time.time())}.txt"
        total = 0

        with open(outp, "w", encoding="latin-1") as f:
            for fn in files:
                src = PADRON_DIR / fn
                for chunk in leer_chunks(src, cols):
                    for row in chunk.itertuples(index=False):
                        f.write("|".join(map(str, row)) + "\n")
                    total += len(chunk)

        opts = [
            {"label": fn, "value": fn}
            for fn in sorted(os.listdir(PADRON_DIR))
            if fn.endswith(".txt")
        ]
        msg = html.Div(
            f"Unificación → {thousand(total)} filas en {outp.name} ✓",
            className="resumen-unificacion"
        )
        return str(outp), opts, msg, ""

    @app.long_callback(
        Output("out-resumen", "children", allow_duplicate=True),
        Output("panel",       "children", allow_duplicate=True),
        Output("st-sum",      "data",     allow_duplicate=True),
        Output("csv-m1",      "data",     allow_duplicate=True),
        Output("csv-dup",     "data",     allow_duplicate=True),
        Output("csv-err",     "data",     allow_duplicate=True),
        Input("btn-anal",     "n_clicks"),
        State("st-unif",      "data"),
        State("archivos",     "value"),
        State("padron",       "value"),
        running=[
            (Output("btn-anal", "disabled"), True, False),
            (Output("btn-dl",   "disabled"), True, False),
        ],
        prevent_initial_call=True,
    )
    def analysis(n_clicks, unif_path, files, tp):
        # determinar fuentes
        if unif_path:
            sources = [Path(unif_path)]
        elif files:
            sources = [PADRON_DIR / fn for fn in files]
        else:
            raise PreventUpdate

        tmp_dir = tempfile.mkdtemp(prefix="anal_", dir=str(CACHE_DIR))

        # archivos de salida
        csv_emp  = Path(tmp_dir) / "Plan_Parcial.csv"
        csv_pami = Path(tmp_dir) / "Multi-CUIT_PAMI.csv"
        csv_osn  = Path(tmp_dir) / "Pluriempleo_OSN.csv"
        csv_dup  = Path(tmp_dir) / "Duplicados.csv"
        csv_err  = Path(tmp_dir) / "Errores.csv"

        if tp == "EMP":
            cols, tablas = COLS_EMP, {}
        else:
            df_ref, tablas = load_references(tp)
            cols = df_ref["campo"].tolist()

        reg2   = re.compile(r"^\d{1,2}$")
        libres = {"discapacidad", "preexistente", "corporativo", "copago"}

        tot_emp = tot_pami = tot_osn = 0
        pp_emp  = m_pami   = m_osn   = 0
        dup_emp = dup_pami = dup_osn = 0
        err_emp = err_pami = err_osn = 0

        pluri_flag  = defaultdict(set)
        dup_counter = Counter()

        # ── Primera pasada ───────────────────
        for src in sources:
            for ch in leer_chunks(src, cols):
                if tp == "EMP":
                    tot_emp += len(ch)
                    mask_pp = ch["tipo_plan"].str.strip() == "P"
                    if mask_pp.any():
                        append_csv(ch[mask_pp], csv_emp)
                        pp_emp += int(mask_pp.sum())
                else:
                    is_pami = ch["codigo_os"].astype(str).str.strip() == "500807"
                    tot_pami += int(is_pami.sum())
                    tot_osn  += len(ch) - int(is_pami.sum())
                    for _, row in ch.iterrows():
                        pluri_flag[(row["cuil_beneficiario"], row["codigo_os"])].add(row["cuit_empleador"])

                for key in zip(*(ch[c] for c in cols[:5])):
                    dup_counter[key] += 1

                for campo, valid in tablas.items():
                    if campo not in ch.columns:
                        continue
                    col = ch[campo].astype(str).str.strip()
                    bad = (~col.isin(valid)) if campo not in libres else (~col.str.match(reg2))
                    if not bad.any():
                        continue
                    df_bad = ch[bad].assign(campo_error=campo)
                    append_csv(df_bad, csv_err)
                    if tp == "EMP":
                        err_emp += int(bad.sum())
                    else:
                        err_pami += int((bad & is_pami).sum())
                        err_osn  += int((bad & ~is_pami).sum())

        # ── Segunda pasada ───────────────────
        if tp != "EMP":
            bad_pluri = {k for k, vs in pluri_flag.items() if len(vs) > 1}
            for src in sources:
                for ch in leer_chunks(src, cols):
                    mask_pl = [
                        tuple(r) in bad_pluri
                        for r in zip(*(ch[c] for c in ("cuil_beneficiario", "codigo_os")))
                    ]
                    if any(mask_pl):
                        df_pl = ch[mask_pl]
                        is_pami = df_pl["codigo_os"].astype(str).str.strip() == "500807"
                        append_csv(df_pl[is_pami],  csv_pami); m_pami += int(is_pami.sum())
                        append_csv(df_pl[~is_pami], csv_osn);  m_osn  += len(df_pl) - int(is_pami.sum())

                    mask_dup = [
                        dup_counter[tuple(r)] > 1
                        for r in zip(*(ch[c] for c in cols[:5]))
                    ]
                    if any(mask_dup):
                        df_d = ch[mask_dup]
                        append_csv(df_d, csv_dup)
                        dup_pami += int((df_d["codigo_os"].astype(str).str.strip()=="500807").sum())
                        dup_osn  += len(df_d) - int((df_d["codigo_os"].astype(str).str.strip()=="500807").sum())
        else:
            for src in sources:
                for ch in leer_chunks(src, cols):
                    mask_dup = [
                        dup_counter[tuple(r)] > 1
                        for r in zip(*(ch[c] for c in cols[:5]))
                    ]
                    if any(mask_dup):
                        append_csv(ch[mask_dup], csv_dup)
                        dup_emp += sum(mask_dup)

        # ── Construcción de resumen y panel ───
        pct = lambda n, t: "0,0%" if t == 0 else f"{n*100/t:.1f}%".replace(",",",")

        if tp == "EMP":
            resumen = html.Div([
                html.H4("Resumen EMP"),
                html.P(f"Total: {thousand(tot_emp)}"),
                html.P(f"Plan Parcial: {thousand(pp_emp)} ({pct(pp_emp, tot_emp)})"),
                html.P(f"Duplicados: {thousand(dup_emp)} ({pct(dup_emp, tot_emp)})"),
                html.P(f"Errores: {thousand(err_emp)} ({pct(err_emp, tot_emp)})"),
            ])
        else:
            resumen = html.Div([
                html.H4("Resumen PAMI"),
                html.P(f"Total: {thousand(tot_pami)}"),
                html.P(f"Multi-CUIT: {thousand(m_pami)} ({pct(m_pami, tot_pami)})"),
                html.P(f"Duplicados: {thousand(dup_pami)} ({pct(dup_pami, tot_pami)})"),
                html.P(f"Errores: {thousand(err_pami)} ({pct(err_pami, tot_pami)})"),
                html.Hr(),
                html.H4("Resumen resto OSN"),
                html.P(f"Total: {thousand(tot_osn)}"),
                html.P(f"Pluriempleo: {thousand(m_osn)} ({pct(m_osn, tot_osn)})"),
                html.P(f"Duplicados: {thousand(dup_osn)} ({pct(dup_osn, tot_osn)})"),
                html.P(f"Errores: {thousand(err_osn)} ({pct(err_osn, tot_osn)})"),
            ])

        def make_table(path: Path):
            df = sample_df(path)
            return dash_table.DataTable(
                df.to_dict("records"),
                [{"name": c, "id": c} for c in df.columns],
                page_size=10
            )

        panel = html.Div([
            html.H4("Plan Parcial" if tp=="EMP" else "Multi-CUIT"),
            make_table(csv_emp if tp=="EMP" else csv_pami), html.Br(),
            html.H4("Pluriempleo") if tp!="EMP" else None,
            make_table(csv_osn)    if tp!="EMP" else None, html.Br(),
            html.H4("Duplicados"), make_table(csv_dup), html.Br(),
            html.H4("Errores"),    make_table(csv_err)
        ])

        summary = {
            "tipo":    tp,
            "tmp_dir": tmp_dir,
            "csv_emp": str(csv_emp),
            "csv_pami":str(csv_pami),
            "csv_osn": str(csv_osn),
            "csv_dup": str(csv_dup),
            "csv_err": str(csv_err),
            "tot_emp":  tot_emp,  "pp_emp":  pp_emp,  "dup_emp":  dup_emp,  "err_emp":  err_emp,
            "tot_pami": tot_pami, "m_pami":   m_pami,  "dup_pami": dup_pami, "err_pami": err_pami,
            "tot_osn":  tot_osn,  "m_osn":    m_osn,   "dup_osn":  dup_osn, "err_osn":  err_osn
        }

        return resumen, panel, summary, summary["csv_emp"], summary["csv_dup"], summary["csv_err"]

    @app.callback(
        Output("dl", "data"),
        Input("btn-dl","n_clicks"),
        State("st-sum","data"),
        prevent_initial_call=True,
    )
    def download(n_clicks, summary):
        if not summary:
            raise PreventUpdate

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            if summary["tipo"] == "EMP":
                for p in (summary["csv_emp"], summary["csv_dup"], summary["csv_err"]):
                    if Path(p).exists():
                        z.write(p, arcname=Path(p).name)
                z.writestr("Resumen_EMP.txt", "\n".join([
                    f"Total: {summary['tot_emp']}",
                    f"Plan Parcial: {summary['pp_emp']}",
                    f"Duplicados: {summary['dup_emp']}",
                    f"Errores: {summary['err_emp']}",
                ]))
            else:
                for p in (summary["csv_pami"], summary["csv_osn"], summary["csv_dup"], summary["csv_err"]):
                    if Path(p).exists():
                        z.write(p, arcname=Path(p).name)
                z.writestr("Resumen_PAMI.txt", "\n".join([
                    f"Total: {summary['tot_pami']}",
                    f"Multi-CUIT: {summary['m_pami']}",
                    f"Duplicados: {summary['dup_pami']}",
                    f"Errores: {summary['err_pami']}",
                ]))
                z.writestr("Resumen_Resto_OSN.txt", "\n".join([
                    f"Total: {summary['tot_osn']}",
                    f"Pluriempleo: {summary['m_osn']}",
                    f"Duplicados: {summary['dup_osn']}",
                    f"Errores: {summary['err_osn']}",
                ]))
        buf.seek(0)
        shutil.rmtree(summary["tmp_dir"], ignore_errors=True)
        return dcc.send_bytes(
            buf.read(),
            filename=f"analisis_{datetime.datetime.now():%Y%m%d_%H%M%S}.zip"
        )

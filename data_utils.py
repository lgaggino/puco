# data_utils.py

"""
data_utils.py – Lógica de acceso y transformación de datos para la app de Padrones.
Contiene:
- lectura en chunks de archivos .txt
- conteo de filas
- muestreo de datos
- append a CSV con pipe-separador
- carga y cache de referencias para validación
"""

import os
import io
import csv
import time
import unicodedata
import re
import tempfile
import shutil
from pathlib import Path
from collections import defaultdict, Counter
from typing import Iterator, List, Tuple, Set, Dict

import pandas as pd
from joblib import Memory

from app.config import PADRON_DIR, REF_DIR, CACHE_DIR, CHUNK_SIZE

# ─────────── Cache para referencias ───────────
_memory = Memory(str(CACHE_DIR), verbose=0)

# ─────────── Helpers de formateo ───────────
thousand = lambda n: f"{n:,}".replace(",", ".")
norm = lambda s: re.sub(
    r"[^0-9A-Za-z]+", "_",
    unicodedata.normalize("NFKD", s)
               .encode("ascii", "ignore")
               .decode()
).strip("_").lower()

# ─────────── Operaciones sobre CSV ───────────
def append_csv(df: pd.DataFrame, path: Path | str) -> None:
    """Agrega df al final de path, creando cabecera si no existe."""
    path = Path(path)
    if df.empty:
        return
    df.to_csv(
        path,
        mode="a",
        header=not path.exists(),
        index=False,
        sep="|",
        quoting=csv.QUOTE_NONE,
        escapechar="\\"
    )

def count_rows(path: Path | str) -> int:
    """Cuenta filas (sin cabecera) en un .txt con encoding latin-1."""
    path = Path(path)
    if not path.exists():
        return 0
    with open(path, encoding="latin-1") as f:
        return max(0, sum(1 for _ in f) - 1)

def sample_df(path: Path | str, n: int = 1000) -> pd.DataFrame:
    """Lee los primeros n registros de un pipe-separated .txt en pandas."""
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="|", nrows=n, dtype="string")

# ─────────── Lectura por chunks ───────────
# Tipos de columna que deben forzarse a string
DFTYPES = {k: "string" for k in (
    "cuil_beneficiario", "cuil_titular", "cuit_empleador",
    "codigo_emp", "codigo_os", "fecha_nacimiento"
)}

def _df(rows: List[List[str]], cols: List[str], vtypes: Dict[str, str]) -> pd.DataFrame:
    """Construye DataFrame de una lista de filas, ajustando tipos y ceros a la izquierda."""
    df = pd.DataFrame(rows, columns=cols, dtype="string")
    if "id_provincia" in df.columns:
        df["id_provincia"] = df["id_provincia"].str.zfill(2).str.strip()
    return df.astype(vtypes, errors="ignore")

def leer_chunks(path: Path | str, cols: List[str]) -> Iterator[pd.DataFrame]:
    """
    Lee path en streaming, devolviendo DataFrames de hasta CHUNK_SIZE filas.
    Maneja líneas partidas por comillas y pipe-separador.
    """
    path = Path(path)
    exp = len(cols)
    buf: List[str] = []
    rows: List[List[str]] = []
    pipes = 0
    vtypes = {c: t for c, t in DFTYPES.items() if c in cols}

    with open(path, "r", encoding="latin-1", errors="ignore") as fh:
        for ln in fh:
            ln = ln.rstrip("\n").strip("'")
            pipes += ln.count("|")
            buf.append(ln)

            if pipes < exp - 1:
                continue
            if pipes == exp - 1:
                parts = "|".join(buf).split("|", exp - 1)
                if len(parts) == exp:
                    parts = [p.strip().strip("'") for p in parts]
                    rows.append(parts)
            buf.clear()
            pipes = 0

            if len(rows) >= CHUNK_SIZE:
                yield _df(rows, cols, vtypes)
                rows.clear()

    if rows:
        yield _df(rows, cols, vtypes)

# ─────────── Carga de referencias ───────────
@_memory.cache
def load_references(tipo: str) -> Tuple[pd.DataFrame, Dict[str, Set[str]]]:
    """
    Carga catálogo de REF_DIR/{EMP,OSN}.csv y devuelve:
    - df de metadatos con columnas normalizadas
    - dict campo → set de valores válidos (incluye ceros sin padding)
    """
    fn = "EMP.csv" if tipo == "EMP" else "OSN.csv"
    raw = Path(REF_DIR, fn).read_text(encoding="latin-1", errors="ignore")
    raw = raw.replace("'\n", "").replace("'", "")
    df = pd.read_csv(io.StringIO(raw), sep=";", dtype=str, engine="python")
    df.columns = [norm(c) for c in df.columns]
    df["campo"] = df["campo"].map(norm)

    tablas: Dict[str, Set[str]] = defaultdict(set)
    for _, row in df.dropna(subset=["referencias"]).iterrows():
        for val in row["referencias"].split(";"):
            key = val.split("=")[0].strip()
            if key:
                tablas[row["campo"]].add(key)
                tablas[row["campo"]].add(key.lstrip("0"))
    return df, tablas


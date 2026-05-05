"""Parser LAS 2.0 robusto sin dependencias externas especializadas."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PATRON_DMS = re.compile(r"(\d+)\D+(\d+)'\s*(\d+(?:\.\d+)?)\"?\s*([NSEW])", re.IGNORECASE)


def _a_float(valor: str) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _dms_a_decimal(texto: str) -> float | None:
    m = PATRON_DMS.search(texto.strip())
    if not m:
        return _a_float(texto)
    grados, minutos, segundos, hemi = m.groups()
    dec = float(grados) + float(minutos) / 60.0 + float(segundos) / 3600.0
    if hemi.upper() in {"W", "S"}:
        dec *= -1.0
    return dec


def _normalizar_headers(headers: list[str]) -> list[str]:
    conteo: Counter[str] = Counter()
    salida: list[str] = []
    for h in headers:
        clave = h.strip().upper() or "CURVA"
        conteo[clave] += 1
        if conteo[clave] > 1:
            salida.append(f"{clave}_{conteo[clave]-1}")
        else:
            salida.append(clave)
    candidatos = [i for i, h in enumerate(salida) if h in {"DEPT", "DEPTH", "TVD", "TVD_1"}]
    if candidatos:
        salida[candidatos[0]] = "DEPTH"
    return salida


def detectar_curvas(columnas: list[str]) -> dict[str, str | None]:
    """Mapea aliases de curvas a nombres canónicos usados por petrofísica."""
    mapa_alias = {
        "GR": ["GR1AFM", "GR1", "GR", "GAM"],
        "RT": ["RPCHM", "RT", "ILD", "LLD", "AT90"],
        "RS": ["RPCSHM", "RS", "LLS", "AT30"],
        "RHOB": ["BDCM", "RHOB", "ZDEN"],
        "NPHI": ["NPCKSM", "NPHI", "TNPH", "CNL"],
        "DT": ["DTLM", "DTHM", "DT", "AC"],
        "CALI": ["CALM", "CALI", "CAL"],
        "BITSIZE": ["BITSIZE", "BS"],
        "PEF": ["DPEM", "PEF"],
    }
    disponibles = {c.upper(): c.upper() for c in columnas}
    out: dict[str, str | None] = {}
    for canonica, aliases in mapa_alias.items():
        out[canonica] = next((a for a in aliases if a in disponibles), None)
    return out


def procesar_las(ruta_archivo: str) -> dict[str, Any]:
    """Retorna {'status', 'metadata', 'data'} donde data es lista de dicts."""
    lineas = Path(ruta_archivo).read_text(encoding="latin-1", errors="ignore").splitlines()
    seccion = ""
    well: dict[str, str] = {}
    curvas: list[str] = []
    headers_a: list[str] = []
    registros: list[list[float]] = []
    wrap_yes = False
    buffer_wrap: list[float] = []

    for ln in lineas:
        raw = ln.strip()
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("~"):
            seccion = raw.upper()
            if seccion.startswith("~A"):
                partes = raw.split()
                headers_a = partes[1:] if len(partes) > 1 else []
            continue

        if seccion.startswith("~V") and "WRAP" in raw.upper():
            wrap_yes = "YES" in raw.upper()

        if seccion.startswith("~W"):
            izq = raw.split(":", 1)[0]
            clave = izq.split(".", 1)[0].strip().upper()
            valor = raw.split(":", 1)[-1].strip() if ":" in raw else izq.split(".", 1)[-1].strip()
            well[clave] = valor
        elif seccion.startswith("~C"):
            token = raw.split(".", 1)[0].strip().upper()
            if token and not token.startswith("~"):
                curvas.append(token)
        elif seccion.startswith("~A"):
            nums = [x for x in re.split(r"\s+", raw) if x]
            fila = [_a_float(x) for x in nums]
            fila = [np.nan if v is None else float(v) for v in fila]
            if wrap_yes:
                buffer_wrap.extend(fila)
                ncols = len(headers_a) or len(curvas)
                while ncols > 0 and len(buffer_wrap) >= ncols:
                    registros.append(buffer_wrap[:ncols])
                    buffer_wrap = buffer_wrap[ncols:]
            else:
                registros.append(fila)

    headers = _normalizar_headers(headers_a or curvas)
    if not headers:
        raise ValueError("No se detectaron curvas en el archivo LAS")
    df = pd.DataFrame(registros)
    if df.shape[1] < len(headers):
        for _ in range(len(headers) - df.shape[1]):
            df[df.shape[1]] = np.nan
    df = df.iloc[:, : len(headers)]
    df.columns = headers

    null_value = _a_float(well.get("NULL", "-999.25"))
    if null_value is not None:
        df = df.replace(null_value, np.nan)

    if "DEPTH" not in df.columns:
        for c in df.columns:
            if c.startswith("TVD"):
                df = df.rename(columns={c: "DEPTH"})
                break
    if "DEPTH" not in df.columns:
        raise ValueError("No se encontró curva de profundidad")

    df = df.sort_values("DEPTH", ascending=True, na_position="last").reset_index(drop=True)

    lat = _dms_a_decimal(well.get("LAT", ""))
    lon = _dms_a_decimal(well.get("LONG", ""))
    curvas_detectadas = detectar_curvas(df.columns.tolist())

    metadata = {
        "pozo": well.get("WELL"),
        "inicio": _a_float(well.get("STRT", "")),
        "fin": _a_float(well.get("STOP", "")),
        "step": _a_float(well.get("STEP", "")),
        "null_value": null_value,
        "n_points": int(len(df)),
        "lat": lat,
        "lon": lon,
        "empresa": well.get("COMP"),
        "campo": well.get("FLD"),
        "pais": well.get("CTRY"),
        "servicio": well.get("SRVC"),
        "fecha": well.get("DATE"),
        "curvas_disponibles": df.columns.tolist(),
        "curvas_detectadas": curvas_detectadas,
    }

    data = df.where(pd.notna(df), None).to_dict(orient="records")
    return {"status": "success", "metadata": metadata, "data": data}

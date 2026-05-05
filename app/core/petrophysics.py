"""Cálculos petrofísicos vectorizados para SpiralGeoLog."""

from __future__ import annotations
from typing import Any
import numpy as np


def _clip01(arr): return np.clip(arr, 0.0, 1.0)
def _igr(gr, gr_min, gr_max):
    return _clip01((np.array(gr, dtype=float) - gr_min) / max(gr_max - gr_min, 1e-12))

def vsh_linear(gr, gr_min, gr_max): return _igr(gr, gr_min, gr_max)
def vsh_larionov_tertiary(gr, gr_min, gr_max):
    return _clip01(0.083 * (2 ** (3.7 * _igr(gr, gr_min, gr_max)) - 1))
def vsh_larionov_older(gr, gr_min, gr_max):
    return _clip01(0.33 * (2 ** (2 * _igr(gr, gr_min, gr_max)) - 1))
def vsh_steiber(gr, gr_min, gr_max):
    igr = _igr(gr, gr_min, gr_max); return _clip01(igr / (3 - 2 * igr + 1e-12))
def vsh_clavier(gr, gr_min, gr_max):
    igr = _igr(gr, gr_min, gr_max)
    return _clip01(1.7 - np.sqrt(np.maximum(3.38 - (igr + 0.7) ** 2, 0.0)))

def phi_density(rhob, rho_ma=2.65, rho_fl=1.0):
    return np.clip((rho_ma - np.array(rhob, dtype=float)) / (rho_ma - rho_fl + 1e-12), 0.0, 0.6)
def phi_neutron(nphi): return np.clip(np.array(nphi, dtype=float), 0.0, 0.6)
def phit(phi_d, phi_n): return np.nanmean(np.vstack([phi_d, phi_n]), axis=0)
def phie(phit_arr, vsh, phi_clay=0.05):
    return np.clip(np.array(phit_arr) - np.array(vsh) * phi_clay, -0.2, 0.6)

def sw_archie(phie, rt, rw=0.025, a=1.0, m=2.0, n=2.0):
    ph = np.maximum(np.array(phie, dtype=float), 1e-6)
    rt = np.maximum(np.array(rt, dtype=float), 1e-6)
    return np.clip(((a * rw) / (rt * (ph ** m))) ** (1.0 / n), 0.0, 1.0)

def sw_simandoux(phie, rt, rw, vsh, rt_sh, a=1, m=2, n=2):
    ph = np.maximum(np.array(phie, dtype=float), 1e-6)
    rt = np.maximum(np.array(rt, dtype=float), 1e-6)
    term = np.array(vsh) / max(rt_sh, 1e-6)
    inv = np.sqrt(term ** 2 + 4 * (a * rw) / (ph ** m * rt))
    return np.clip(((inv - term) / 2) ** (2.0 / n), 0.0, 1.0)

def k_timur(phie, swirr=0.25):
    return np.clip(0.136 * (np.maximum(np.array(phie), 0) ** 4.4) / (max(swirr, 1e-6) ** 2) * 1000, 0, None)
def k_kozeny(phie, grain_size=0.1):
    ph = np.clip(np.array(phie, dtype=float), 1e-6, 0.6)
    return np.clip((grain_size ** 2) * (ph ** 3) / ((1 - ph) ** 2 + 1e-12) * 1e4, 0, None)

def pay_score(vsh, phie, sw, rt, k, washout=0) -> int:
    s = (25 * (1 - np.clip(vsh, 0, 1))
       + 25 * np.clip(phie / 0.3, 0, 1)
       + 25 * (1 - np.clip(sw, 0, 1))
       + 15 * np.clip(np.log10(max(rt, 1e-6)) / np.log10(50), 0, 1)
       + 10 * np.clip(np.log10(max(k, 1e-6)) / np.log10(200), 0, 1)
       - 5 * max(washout, 0))
    return int(np.clip(round(s), 0, 100))

def calcular_todo(data: list[dict], metadata: dict, params: dict | None = None) -> dict[str, Any]:
    params = params or {}
    arr = {k: np.array([row.get(k) for row in data], dtype=float)
           for k in (data[0].keys() if data else [])}
    curv = metadata.get("curvas_detectadas", {})

    # FIX CRÍTICO: depth directo de arr — curvas_detectadas no tiene clave DEPTH
    depth = arr.get("DEPTH", np.full(len(data), np.nan))
    get = lambda c: arr.get(curv.get(c, ""), np.full(len(data), np.nan))
    gr, rt, rs, rhob, nphi, dt, cali, bitsize = (
        get("GR"), get("RT"), get("RS"), get("RHOB"),
        get("NPHI"), get("DT"), get("CALI"), get("BITSIZE")
    )

    gr_min, gr_max = np.nanpercentile(gr, 5), np.nanpercentile(gr, 95)
    vsh = vsh_larionov_tertiary(gr, gr_min, gr_max)

    phi_d = (phi_density(rhob, params.get("rho_ma", 2.65))
             if np.isfinite(rhob).any() else np.full(len(data), np.nan))
    phi_n = (phi_neutron(nphi)
             if np.isfinite(nphi).any() else np.full(len(data), np.nan))
    phit_arr = (phit(phi_d, phi_n)
                if np.isfinite(phi_d).any() and np.isfinite(phi_n).any()
                else np.full(len(data), np.nan))
    phie_arr = (phie(phit_arr, vsh)
                if np.isfinite(phit_arr).any() else np.full(len(data), np.nan))
    sw = (sw_archie(phie_arr, rt,
                    rw=params.get("rw", 0.025), a=params.get("a", 1.0),
                    m=params.get("m", 2.0),     n=params.get("n", 2.0))
          if np.isfinite(phie_arr).any() and np.isfinite(rt).any()
          else np.full(len(data), np.nan))
    k = (k_timur(phie_arr, swirr=params.get("swirr", 0.25))
         if np.isfinite(phie_arr).any() else np.full(len(data), np.nan))

    washout = np.where(np.isfinite(cali) & np.isfinite(bitsize),
                       np.maximum(cali - bitsize, 0), 0)
    gas = np.where(np.isfinite(phi_n) & np.isfinite(phi_d),
                   phi_n - phi_d > 0.08, False)
    score = np.array([
        pay_score(
            vsh[i],
            phie_arr[i] if np.isfinite(phie_arr[i]) else 0,
            sw[i]       if np.isfinite(sw[i])        else 1,
            rt[i]       if np.isfinite(rt[i])         else 0.2,
            k[i]        if np.isfinite(k[i])          else 0,
            washout[i]
        )
        for i in range(len(data))
    ])

    conv = lambda x: [None if not np.isfinite(v) else float(v) for v in x]
    return {
        "depth":   conv(depth),  "gr":    conv(gr),   "rt":  conv(rt),
        "rs":      conv(rs),     "rhob":  conv(rhob), "nphi":conv(nphi),
        "dt":      conv(dt),     "cali":  conv(cali),
        "vsh":     conv(vsh),    "phi_d": conv(phi_d),"phi_n":conv(phi_n),
        "phit":    conv(phit_arr),"phie": conv(phie_arr),
        "sw":      conv(sw),     "k":     conv(k),
        "score":   score.tolist(),"gas":  gas.tolist(),"washout":conv(washout),
        "params_used": {
            "rw": params.get("rw",0.025), "a": params.get("a",1.0),
            "m":  params.get("m",2.0),    "n": params.get("n",2.0),
            "rho_ma":     params.get("rho_ma","larionov_tertiary"),
            "vsh_method": params.get("vsh_method","larionov_tertiary"),
            "sw_method":  params.get("sw_method","archie"),
            "gr_min": float(gr_min), "gr_max": float(gr_max),
        }
    }

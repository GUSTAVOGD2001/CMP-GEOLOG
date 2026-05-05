"""Detección de intervalos candidatos a hidrocarburo."""
from __future__ import annotations
import numpy as np

def _clas(score, sw):
    if score >= 75 and sw < 0.40: return "EXCELLENT_PAY"
    if score >= 60 and sw < 0.55: return "GOOD_PAY"
    if score >= 45: return "MARGINAL_PAY"
    return "NON_PAY"

def detectar_zonas(petro: dict, params: dict | None = None) -> list[dict]:
    params = params or {}
    d=np.array(petro.get("depth",[]),dtype=float); v=np.array(petro.get("vsh",[]),dtype=float); p=np.array(petro.get("phie",[]),dtype=float); s=np.array(petro.get("sw",[]),dtype=float)
    rt=np.array(petro.get("rt",[]),dtype=float); k=np.array(petro.get("k",[]),dtype=float); sc=np.array(petro.get("score",[]),dtype=float); gas=np.array(petro.get("gas",[]),dtype=bool)
    cand=(v<params.get("vsh_max",0.35))&(p>params.get("phie_min",0.08))&(s<params.get("sw_max",0.60))&np.isfinite(d)
    zonas=[]; i=0
    while i<len(d):
        if not cand[i]: i+=1; continue
        j=i
        while j+1<len(d) and cand[j+1]: j+=1
        top, base=float(d[i]), float(d[j]); thick=base-top
        if thick>=params.get("espesor_min",5.0):
            zonas.append({"top":round(top,2),"base":round(base,2),"thick":round(thick,2),"vsh":float(np.nanmean(v[i:j+1])),"phie":float(np.nanmean(p[i:j+1])),"sw":float(np.nanmean(s[i:j+1])),"rt":float(np.nanmean(rt[i:j+1])),"k":float(np.nanmean(k[i:j+1])),"score":float(np.nanmean(sc[i:j+1])),"gas_crossover":bool(np.any(gas[i:j+1])),"classification":_clas(float(np.nanmean(sc[i:j+1])), float(np.nanmean(s[i:j+1])))})
        i=j+1
    return zonas

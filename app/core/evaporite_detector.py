"""Detección de evaporitas para filtrar falsos positivos."""
from __future__ import annotations
import numpy as np

def detectar_evaporitas(petro: dict) -> dict:
    d=np.array(petro.get("depth",[]),dtype=float); gr=np.array(petro.get("gr",[]),dtype=float); rhob=np.array(petro.get("rhob",[]),dtype=float); nphi=np.array(petro.get("nphi",[]),dtype=float)
    if not np.isfinite(rhob).any():
        return {"halite":[],"anhydrite":[],"gypsum":[],"any_evaporite":False,"warning":"Sin RHOB - detección no disponible"}
    hal=(rhob>=1.95)&(rhob<=2.15)&(nphi<0.02)&(gr<25)
    anh=(rhob>2.85)&(nphi<0.01)&(gr<15)
    gyp=(rhob>=2.2)&(rhob<=2.5)&(nphi>0.40)&(gr<20)
    f=lambda m:[float(x) for x in d[m & np.isfinite(d)]]
    return {"halite":f(hal),"anhydrite":f(anh),"gypsum":f(gyp),"any_evaporite":bool(np.any(hal|anh|gyp))}

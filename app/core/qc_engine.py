"""Motor de control de calidad por profundidad."""
from __future__ import annotations
import numpy as np

def run_qc(petro: dict) -> list[dict]:
    d    = np.array(petro.get("depth",  []), dtype=float)
    sw   = np.array(petro.get("sw",     []), dtype=float)
    phie = np.array(petro.get("phie",   []), dtype=float)
    rhob = np.array(petro.get("rhob",   []), dtype=float)
    nphi = np.array(petro.get("nphi",   []), dtype=float)
    cali = np.array(petro.get("cali",   []), dtype=float)
    rt   = np.array(petro.get("rt",     []), dtype=float)
    gr   = np.array(petro.get("gr",     []), dtype=float)
    wo_list = petro.get("washout", [])  # FIX: leer washout calculado
    out = []
    for i, dep in enumerate(d):
        if not np.isfinite(dep): continue
        if np.isfinite(sw[i])   and sw[i] > 1.0:
            out.append({"depth":float(dep),"type":"ERROR",   "code":"SW_OVERFLOW", "message":"Sw > 1.0"})
        if np.isfinite(phie[i]) and phie[i] < 0:
            out.append({"depth":float(dep),"type":"ERROR",   "code":"NEG_POROSITY","message":"PHIE negativa"})
        if np.isfinite(rhob[i]) and rhob[i] < 1.5:
            out.append({"depth":float(dep),"type":"WARNING", "code":"LOW_RHOB",    "message":"RHOB extremadamente baja"})
        if np.isfinite(rhob[i]) and rhob[i] > 3.0:
            out.append({"depth":float(dep),"type":"WARNING", "code":"HIGH_RHOB",   "message":"RHOB alta - posible anhidrita"})
        if np.isfinite(nphi[i]) and nphi[i] < -0.02:
            out.append({"depth":float(dep),"type":"WARNING", "code":"NEG_NPHI",    "message":"NPHI negativa"})
        if np.isfinite(rt[i])   and rt[i] > 5000:
            out.append({"depth":float(dep),"type":"INFO",    "code":"EXTREME_RT",  "message":"RT extrema"})
        wo_val = float(wo_list[i]) if i < len(wo_list) and wo_list[i] is not None else 0.0
        if np.isfinite(cali[i]) and wo_val > 2.0:
            out.append({"depth":float(dep),"type":"WARNING", "code":"WASHOUT",
                        "message":f"Agujero agrandado {round(wo_val,1)} in"})
        if (np.isfinite(rhob[i]) and np.isfinite(nphi[i]) and np.isfinite(gr[i])
                and 1.95<=rhob[i]<=2.15 and nphi[i]<0.02 and gr[i]<25):
            out.append({"depth":float(dep),"type":"CRITICAL","code":"SALT_DOME",
                        "message":"Firma diagnóstica de halita"})
    return out

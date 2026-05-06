"""Clasificación litológica punto a punto con descripción interpretativa."""
from __future__ import annotations
import numpy as np

LITHO_CODES = {
    0: "lutita",
    1: "arena_limpia",
    2: "arena_arcillosa",
    3: "caliza",
    4: "dolomita",
    5: "evaporita",
    6: "carbon",
    7: "arena_gas",
}

LITHO_COLORS = {
    "lutita":          "#6b7280",
    "arena_limpia":    "#fbbf24",
    "arena_arcillosa": "#84a35a",
    "caliza":          "#93c5fd",
    "dolomita":        "#818cf8",
    "evaporita":       "#f87171",
    "carbon":          "#1f2937",
    "arena_gas":       "#fb923c",
}

LITHO_LABELS = {
    "lutita":          "Lutita",
    "arena_limpia":    "Arena limpia",
    "arena_arcillosa": "Arena arcillosa",
    "caliza":          "Caliza",
    "dolomita":        "Dolomita",
    "evaporita":       "Evaporita / Sal",
    "carbon":          "Carbón",
    "arena_gas":       "Arena con gas",
}


def _clasificar_punto(vsh, rhob, nphi, gr, phie, gas_flag, score):
    has_rhob = not (rhob != rhob or rhob is None)
    has_nphi = not (nphi != nphi or nphi is None)

    if has_rhob and has_nphi:
        if 1.95 <= rhob <= 2.15 and nphi < 0.02 and gr < 25:
            return "evaporita", (
                f"Halita (domo salino): RHOB={rhob:.3f} g/cc, NPHI={nphi:.3f} — "
                "FALSO POSITIVO petrofísico. Alta resistividad no indica HC."
            )
        if rhob > 2.85 and nphi < 0.01 and gr < 15:
            return "evaporita", (
                f"Anhidrita: RHOB={rhob:.3f} g/cc, NPHI~0, GR<15 — "
                "evaporita densa, no reservorio."
            )

    if has_rhob and rhob < 1.80 and gr < 35:
        return "carbon", (
            f"Carbón: RHOB={rhob:.3f} g/cc (muy bajo), GR={gr:.0f} API — "
            "carbón o lignito, no reservorio clástico."
        )

    if has_rhob and has_nphi and rhob > 2.68 and nphi < 0.15 and vsh < 0.25 and gr < 35:
        if rhob > 2.80:
            return "dolomita", (
                f"Dolomita: RHOB={rhob:.3f} g/cc, NPHI={nphi:.3f}, GR={gr:.0f} API — "
                f"carbonato dolomítico. PHIE={phie:.3f}. "
                + ("Posible reservorio si hay fracturas." if phie > 0.05 else "Porosidad muy baja.")
            )
        return "caliza", (
            f"Caliza: RHOB={rhob:.3f} g/cc, NPHI={nphi:.3f}, GR={gr:.0f} API — "
            f"carbonato calcítico. PHIE={phie:.3f}. "
            + ("Reservorio potencial." if phie > 0.08 else "Porosidad baja.")
        )

    if vsh is None or vsh != vsh:
        return "lutita", "Sin datos de GR para clasificar — asumido lutita."

    if vsh >= 0.50:
        return "lutita", (
            f"Lutita: VSH={vsh:.3f} — alto contenido de arcilla ({vsh*100:.0f}%). "
            "Sello potencial para trampas estructurales."
        )
    if vsh >= 0.35:
        return "lutita", (
            f"Lutita arenosa: VSH={vsh:.3f} — arcillosa ({vsh*100:.0f}% arcilla). "
            "No productiva, posible sello marginal."
        )
    if vsh >= 0.15:
        return "arena_arcillosa", (
            f"Arena arcillosa: VSH={vsh:.3f} ({vsh*100:.0f}% arcilla). "
            f"PHIE={phie:.3f}. "
            + ("Reservorio de calidad media, puede producir con estimulación."
               if phie > 0.10 else "Porosidad reducida por arcilla.")
        )

    if gas_flag:
        return "arena_gas", (
            f"Arena con gas: VSH={vsh:.3f} (arena muy limpia), "
            f"crossover densidad-neutrón detectado — "
            f"PHIE={phie:.3f}. Indicador directo de gas. "
            + (f"Score={score:.0f}/100." if score else "")
        )

    return "arena_limpia", (
        f"Arena limpia: VSH={vsh:.3f} ({vsh*100:.0f}% arcilla). "
        f"PHIE={phie:.3f}. "
        + (f"Excelente reservorio, score={score:.0f}/100." if score >= 70
           else f"Buen reservorio, score={score:.0f}/100." if score >= 50
           else f"Reservorio potencial, score={score:.0f}/100.")
    )


def calcular_litologia(petro: dict) -> tuple[list[str], list[str]]:
    n = len(petro.get("depth", []))

    def arr(key):
        raw = petro.get(key, [])
        return [x if x is not None else float("nan") for x in raw]

    vsh   = arr("vsh")
    rhob  = arr("rhob")
    nphi  = arr("nphi")
    gr    = arr("gr")
    phie  = arr("phie")
    gas   = petro.get("gas",   [False] * n)
    score = petro.get("score", [0]     * n)

    codes, descs = [], []
    for i in range(n):
        code, desc = _clasificar_punto(
            vsh[i]   if i < len(vsh)   else float("nan"),
            rhob[i]  if i < len(rhob)  else float("nan"),
            nphi[i]  if i < len(nphi)  else float("nan"),
            gr[i]    if i < len(gr)    else float("nan"),
            phie[i]  if i < len(phie)  else float("nan"),
            bool(gas[i])    if i < len(gas)   else False,
            float(score[i]) if i < len(score) else 0.0,
        )
        codes.append(code)
        descs.append(desc)

    return codes, descs


def litho_summary(codes: list[str]) -> dict:
    total = len(codes)
    if total == 0:
        return {}
    from collections import Counter
    counts = Counter(codes)
    return {
        k: {
            "count": v,
            "pct":   round(100 * v / total, 1),
            "label": LITHO_LABELS.get(k, k),
            "color": LITHO_COLORS.get(k, "#888"),
        }
        for k, v in sorted(counts.items(), key=lambda x: -x[1])
    }

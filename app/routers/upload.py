"""Router de carga y procesamiento LAS."""
from __future__ import annotations
import os, tempfile
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from app.core.las_parser import procesar_las
from app.core.petrophysics import calcular_todo
from app.core.zone_detector import detectar_zonas
from app.core.evaporite_detector import detectar_evaporitas
from app.core.qc_engine import run_qc
from app.core.litho_classifier import (
    calcular_litologia, litho_summary, LITHO_COLORS, LITHO_LABELS
)

router = APIRouter(tags=["upload"])

@router.post('/upload-las')
async def upload_las(
    file: UploadFile = File(...),
    downsample: int = Query(5, ge=1, le=100)
) -> dict:
    if not file.filename or not file.filename.lower().endswith('.las'):
        raise HTTPException(status_code=400, detail='Solo se aceptan archivos .las')

    contenido = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.las') as tmp:
        tmp.write(contenido)
        ruta = tmp.name

    try:
        parsed = procesar_las(ruta)
        petro  = calcular_todo(parsed['data'], parsed['metadata'])
        zonas  = detectar_zonas(petro)
        evap   = detectar_evaporitas(petro)
        qc     = run_qc(petro)

        litho_codes, litho_descs = calcular_litologia(petro)
        summary = litho_summary(litho_codes)

        for k, v in list(petro.items()):
            if isinstance(v, list):
                petro[k] = v[::downsample]

        litho_codes_ds = litho_codes[::downsample]
        litho_descs_ds = litho_descs[::downsample]

        return {
            "status":          "success",
            "metadata":        parsed['metadata'],
            "petrophysics":    petro,
            "zones":           zonas,
            "evaporite_flags": evap,
            "qc_flags":        qc,
            "lithology": {
                "codes":        litho_codes_ds,
                "descriptions": litho_descs_ds,
                "colors":       LITHO_COLORS,
                "labels":       LITHO_LABELS,
                "summary":      summary,
            },
        }
    finally:
        os.unlink(ruta)

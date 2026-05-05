from app.core.las_parser import procesar_las

def test_procesar_las_sintetico(tmp_path):
    contenido = """~Version
VERS. 2.0 : LAS
WRAP. NO
~Well
STRT.M 1000
STOP.M 1001
STEP.M 0.5
NULL. -999.25
WELL. TLENSE-1EXP-V
COMP. PEMEX
FLD . TLENSE
SRVC. Baker Hughes Company
LAT . 18° 54' 51.025\" N
LONG. 93° 10' 26.097\" W
DATE. 2022/01/07
~Curve
DEPT.M : Depth
TVD .M : TVD duplicado
TVD .M : TVD duplicado 2
GR1AFM.API : Gamma
RPCHM.OHM : RT
~A DEPT TVD TVD GR1AFM RPCHM
1001 1001 1001 60 2
1000 1000 1000 50 3
"""
    p = tmp_path / 'x.las'; p.write_text(contenido, encoding='latin-1')
    out = procesar_las(str(p))
    md = out['metadata']
    assert md['pozo'] == 'TLENSE-1EXP-V'
    assert round(md['lat'], 4) == 18.9142
    assert round(md['lon'], 4) == -93.1739
    assert out['data'][0]['DEPTH'] == 1000.0
    assert 'TVD_1' in md['curvas_disponibles']

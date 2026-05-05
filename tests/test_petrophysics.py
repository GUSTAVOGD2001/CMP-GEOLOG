import numpy as np
from app.core.petrophysics import vsh_larionov_tertiary, phi_density, sw_archie, pay_score

def test_vsh_larionov_tertiary_rango():
    vals = vsh_larionov_tertiary([100, 50, 0], 0, 100)
    assert np.all(vals >= 0) and np.all(vals <= 1)

def test_phi_density_limites():
    assert phi_density(2.65, rho_ma=2.65) == 0.0
    assert phi_density(1.0, rho_ma=2.65, rho_fl=1.0) == 0.6

def test_sw_archie_objetivo():
    val = float(sw_archie(0.20, 10, rw=0.025))
    assert 0.17 <= val <= 0.19

def test_pay_score_extremos():
    assert pay_score(0.05, 0.30, 0.20, 50, 200, 0) == 100
    assert pay_score(0.50, 0.05, 0.90, 1, 0, 5) == 0

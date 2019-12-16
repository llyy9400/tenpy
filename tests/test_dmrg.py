"""A collection of tests to check the functionality of `tenpy.dmrg`"""
# Copyright 2018-2019 TeNPy Developers, GNU GPLv3

import itertools as it
import tenpy.linalg.np_conserved as npc
from tenpy.models.tf_ising import TFIChain
from tenpy.models.spins import SpinChain
from tenpy.algorithms import dmrg
from tenpy.algorithms.exact_diag import ExactDiag
from tenpy.networks import mps
import pytest
import numpy as np
from scipy import integrate


def e0_tranverse_ising(g=0.5):
    """Exact groundstate energy of transverse field Ising.

    H = - J sigma_z sigma_z + g sigma_x
    Can be obtained by mapping to free fermions.
    """
    return integrate.quad(_f_tfi, 0, np.pi, args=(g, ))[0]


def _f_tfi(k, g):
    return -2 * np.sqrt(1 + g**2 - 2 * g * np.cos(k)) / np.pi / 2.


params = [
    ('finite', True, True, 1),  # 1-site DMRG with mixer=False is expected to fail.
    ('finite', True, True, 2),
    ('finite', True, False, 2),
    ('finite', False, True, 1),
    ('finite', False, True, 2),
    ('finite', False, False, 2),
    ('infinite', True, True, 1),
    ('infinite', True, True, 2),
    ('infinite', True, False, 2),
    ('infinite', False, True, 1),
    ('infinite', False, True, 2),
    ('infinite', False, False, 2)
]


@pytest.mark.parametrize("bc_MPS, combine, mixer, n", params)
@pytest.mark.slow
def test_dmrg(bc_MPS, combine, mixer, n, L=4, g=1.5):
    model_params = dict(L=L, J=1., g=g, bc_MPS=bc_MPS, conserve=None, verbose=0)
    M = TFIChain(model_params)
    state = [0] * L  # Ferromagnetic Ising
    psi = mps.MPS.from_product_state(M.lat.mps_sites(), state, bc=bc_MPS)
    dmrg_pars = {
        'verbose': 5,
        'combine': combine,
        'mixer': mixer,
        'chi_list': {
            0: 10,
            5: 30
        },
        'max_E_err': 1.e-12,
        'max_S_err': 1.e-8,
        'N_sweeps_check': 4,
        'mixer_params': {
            'disable_after': 15,
            'amplitude': 1.e-5
        },
        'trunc_params': {
            'svd_min': 1.e-10,
        },
        'lanczos_params': {
            'reortho': True,
            'N_cache': 20
        },
        'max_sweeps': 40,
        'active_sites': n,
    }
    if not mixer:
        del dmrg_pars['mixer_params']  # avoid warning of unused parameter
    if bc_MPS == 'infinite':
        # if mixer is not None:
        #     dmrg_pars['mixer_params']['amplitude'] = 1.e-12  # don't actually contribute...
        dmrg_pars['start_env'] = 1
    res = dmrg.run(psi, M, dmrg_pars)
    if bc_MPS == 'finite':
        ED = ExactDiag(M)
        ED.build_full_H_from_mpo()
        ED.full_diagonalization()
        E_ED, psi_ED = ED.groundstate()
        ov = npc.inner(psi_ED, ED.mps_to_full(psi), 'range', do_conj=True)
        print("E_DMRG={Edmrg:.14f} vs E_exact={Eex:.14f}".format(Edmrg=res['E'], Eex=E_ED))
        print("compare with ED: overlap = ", abs(ov)**2)
        assert abs(abs(ov) - 1.) < 1.e-10  # unique groundstate: finite size gap!
    else:
        # compare exact solution for transverse field Ising model
        Edmrg = res['E']
        Eexact = e0_tranverse_ising(g)
        print("E_DMRG={Edmrg:.12f} vs E_exact={Eex:.12f}".format(Edmrg=Edmrg, Eex=Eexact))
        print("relative energy error: {err:.2e}".format(err=abs((Edmrg - Eexact) / Eexact)))
        print("norm err:", psi.norm_test())
        Edmrg2 = np.mean(psi.expectation_value(M.H_bond))
        Edmrg3 = M.H_MPO.expectation_value(psi)
        assert abs((Edmrg - Eexact) / Eexact) < 1.e-10
        assert abs((Edmrg - Edmrg2) / Edmrg2) < max(1.e-10, np.max(psi.norm_test()))
        assert abs((Edmrg - Edmrg3) / Edmrg3) < max(1.e-10, np.max(psi.norm_test()))


@pytest.mark.slow
def test_dmrg_rerun(L=2):
    bc_MPS = 'infinite'
    model_params = dict(L=L, J=1., g=1.5, bc_MPS=bc_MPS, conserve=None, verbose=0)
    M = TFIChain(model_params)
    psi = mps.MPS.from_product_state(M.lat.mps_sites(), [0] * L, bc=bc_MPS)
    dmrg_pars = {'verbose': 5, 'chi_list': {0: 5, 5: 10}, 'N_sweeps_check': 4, 'combine': True}
    eng = dmrg.TwoSiteDMRGEngine(psi, M, dmrg_pars)
    E1, _ = eng.run()
    assert abs(E1 - -1.67192622) < 1.e-6
    model_params['g'] = 1.3
    M = TFIChain(model_params)
    del eng.engine_params['chi_list']
    new_chi = 15
    eng.engine_params['trunc_params']['chi_max'] = new_chi
    eng.init_env(M)
    E2, psi = eng.run()
    assert max(psi.chi) == new_chi
    assert abs(E2 - -1.50082324) < 1.e-6


params = [('TwoSiteDMRGEngine', 'lanczos'), ('TwoSiteDMRGEngine', 'arpack'),
          ('TwoSiteDMRGEngine', 'ED_block'), ('TwoSiteDMRGEngine', 'ED_all'),
          ('SingleSiteDMRGEngine', 'ED_block')]


@pytest.mark.slow
@pytest.mark.parametrize("engine, diag_method", params)
def test_dmrg_diag_method(engine, diag_method, tol=1.e-6):
    bc_MPS = 'finite'
    model_params = dict(L=6, S=0.5, bc_MPS=bc_MPS, conserve='Sz', verbose=0)
    M = SpinChain(model_params)
    # chose total Sz= 4, not 3=6/2, i.e. not the sector with lowest energy!
    # make sure below that we stay in that sector, if we're supposed to.
    init_Sz_4 = ['up', 'down', 'up', 'up', 'up', 'down']
    psi_Sz_4 = mps.MPS.from_product_state(M.lat.mps_sites(), init_Sz_4, bc=bc_MPS)
    dmrg_pars = {
        'verbose': 1,
        'N_sweeps_check': 1,
        'combine': True,
        'max_sweeps': 5,
        'diag_method': diag_method,
        'mixer': True,
    }
    ED = ExactDiag(M)
    ED.build_full_H_from_mpo()
    ED.full_diagonalization()
    if diag_method == "ED_all":
        charge_sector = None  # allow to change the sector
    else:
        charge_sector = [2]  # don't allow to change the sector
    E_ED, psi_ED = ED.groundstate(charge_sector=charge_sector)

    DMRGEng = dmrg.__dict__.get(engine)
    print("DMRGEng = ", DMRGEng)
    print("setting diag_method = ", dmrg_pars['diag_method'])
    eng = DMRGEng(psi_Sz_4.copy(), M, dmrg_pars)
    E0, psi0 = eng.run()
    print("E0 = {0:.15f}".format(E0))
    assert abs(E_ED - E0) < tol
    ov = npc.inner(psi_ED, ED.mps_to_full(psi0), 'range', do_conj=True)
    assert abs(abs(ov) - 1) < tol


@pytest.mark.slow
def test_dmrg_excited(eps=1.e-12):
    # checks ground state and 2 excited states (in same symmetry sector) for a small system
    # (without truncation)
    L, g = 8, 1.3
    bc = 'finite'
    model_params = dict(L=L, J=1., g=g, bc_MPS=bc, conserve='parity', verbose=0)
    M = TFIChain(model_params)
    # compare to exact solution
    ED = ExactDiag(M)
    ED.build_full_H_from_mpo()
    ED.full_diagonalization()
    # Note: energies sorted by chargesector (first 0), then ascending -> perfect for comparison
    print("Exact diag: E[:5] = ", ED.E[:5])
    print("Exact diag: (smalles E)[:10] = ", np.sort(ED.E)[:10])

    psi_ED = [ED.V.take_slice(i, 'ps*') for i in range(5)]
    print("charges : ", [psi.qtotal for psi in psi_ED])

    # first DMRG run
    psi0 = mps.MPS.from_product_state(M.lat.mps_sites(), [0] * L, bc=bc)
    dmrg_pars = {
        'verbose': 0,
        'N_sweeps_check': 1,
        'lanczos_params': {
            'reortho': False
        },
        'diag_method': 'lanczos',
        'combine': True
    }
    eng0 = dmrg.TwoSiteDMRGEngine(psi0, M, dmrg_pars)
    E0, psi0 = eng0.run()
    assert abs((E0 - ED.E[0]) / ED.E[0]) < eps
    ov = npc.inner(psi_ED[0], ED.mps_to_full(psi0), 'range', do_conj=True)
    assert abs(abs(ov) - 1.) < eps  # unique groundstate: finite size gap!
    # second DMRG run for first excited state
    dmrg_pars['verbose'] = 1.
    dmrg_pars['orthogonal_to'] = [psi0]
    psi1 = mps.MPS.from_product_state(M.lat.mps_sites(), [0] * L, bc=bc)
    eng1 = dmrg.TwoSiteDMRGEngine(psi1, M, dmrg_pars)
    E1, psi1 = eng1.run()
    assert abs((E1 - ED.E[1]) / ED.E[1]) < eps
    ov = npc.inner(psi_ED[1], ED.mps_to_full(psi1), 'range', do_conj=True)
    assert abs(abs(ov) - 1.) < eps  # unique groundstate: finite size gap!
    # and a third one to check with 2 eigenstates
    dmrg_pars['orthogonal_to'] = [psi0, psi1]
    # note: different intitial state necessary, otherwise H is 0
    psi2 = mps.MPS.from_singlets(psi0.sites[0], L, [(0, 1), (2, 3), (4, 5), (6, 7)], bc=bc)
    eng2 = dmrg.TwoSiteDMRGEngine(psi2, M, dmrg_pars)
    E2, psi2 = eng2.run()
    print(E2)
    assert abs((E2 - ED.E[2]) / ED.E[2]) < eps
    ov = npc.inner(psi_ED[2], ED.mps_to_full(psi2), 'range', do_conj=True)
    assert abs(abs(ov) - 1.) < eps  # unique groundstate: finite size gap!


def test_chi_list():
    assert dmrg.chi_list(3) == {0: 3}
    assert dmrg.chi_list(12, 12, 5) == {0: 12}
    assert dmrg.chi_list(24, 12, 5) == {0: 12, 5: 24}
    assert dmrg.chi_list(27, 12, 5) == {0: 12, 5: 24, 10: 27}

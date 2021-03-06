[latest]
========

Release Notes
-------------
This release contains a major update of the documentation, which is now hosted by "Read the Docs" at https://tenpy.readthedocs.io/.
Update your bookmark :-)

Apart from that, this release introduces a format how to save and load data (in particular TeNPy classes) to HDF5 files.
See :doc:`/intro/input_output` for more details.
To use that feature, you need to **install** the h5py package (and therefore some version of the HDF5 library).
This is easy with anaconda, ``conda install h5py``, but might be cumbersome on your local computing cluster.
(However, many university computing clusters have some version of HDF5 installed already. Check with your local sysadmin.)

Changelog
---------

Backwards incompatible changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- Remove argument `leg0` from :class:`~tenpy.networks.mpo.MPOGraph.build_MPO`.
- Remove argument `leg0` from :class:`~tenpy.networks.mpo.MPO.from_grids`, instead optionally give *all* `legs` as argument.
- Don't save `H_MPO_graph` as model attribute anymore - this also wasn't documented.
- Renamed the truncation parameter `symmetry_tol` to `degeneracy_tol` and make the criterion more reasonable by not 
  checking :math:`log(S_i/S_j) < log(symmetry_tol)`, but simply :math:`log(S_i/S_j) < degeneracy_tol``.
  The latter makes more sense, as it is equivalent to 
  :math:`(S_i - S_j)/S_j < exp(degeneracy_tol) - 1 = degeneracy_tol + \mathcal{O}(degeneracy_tol^2)`.
- Deprecated :meth:`tenpy.networks.mps.MPS.increase_L` in favor of the newly added
  :meth:`tenpy.networks.mps.MPS.enlarge_MPS_unit_cell` (taking ``factor`` instead of ``new_L=factor*L`` as argument).
- :meth:`tenpy.networks.mps.MPS.correlation_function` now auto-determines whether a Jordan-Wigner string is necessary.
  If any of the given operators is directly an npc Array, it will now raise an error; set ``autoJW=False`` in that case.

Added
^^^^^
- :mod:`tenpy.tools.hdf5_io` with convenience functions for import and output with pickle, as well as an implementation 
  allowing to save and load objects to HDF5 files in the format specified in :doc:`/intro/input_output`.
- human-readable `boundary_conditions` property in :class:`~tenpy.models.lattice.Lattice`.
- `save_hdf5` and `load_hdf5` methods to support saving/loading to HDF5 for the following classes (and their subclasses):
  - :class:`~tenpy.linalg.charges.ChargeInfo`
  - :class:`~tenpy.linalg.charges.LegCharge`
  - :class:`~tenpy.linalg.charges.LegPipe`
  - :class:`~tenpy.linalg.np_conserved.Array`
  - :class:`~tenpy.networks.mps.MPS`
  - :class:`~tenpy.networks.mpo.MPO`
  - :class:`~tenpy.models.lattice.Lattice`
- Argument `insert_all_id` for :meth:`tenpy.networks.mpo.MPOGraph.from_terms` and :meth:`~tenpy.networks.mpo.MPOGraph.from_term_list`
- :meth:`tenpy.networks.mps.MPSEnvironment.get_initialization_data` for a convenient way of saving the necessary parts of the environment after an DMRG run.
- Method `enlarge_MPS_unit_cell` for the following classes:
  - :class:`~tenpy.networks.mps.MPS`
  - :class:`~tenpy.networks.mpo.MPO`
  - :class:`~tenpy.models.lattice.Lattice`
  - :class:`~tenpy.models.model.Model`, :class:`~tenpy.models.model.MPOModel`, :class:`~tenpy.models.model.MPSModel`
- :func:`tenpy.tools.misc.to_iterable_of_len` for convenience of handling arguments.
- :meth:`tenpy.models.lattice.Lattice.mps2lat_values_masked` as generalization of :meth:`tenpy.models.lattice.Lattice.mps2lat_values`.

Changed
^^^^^^^
- DEFAULT DMRG paramter ``'diag_method'`` from ``'lanczos'`` to ``'default'``, which is the same for large bond
  dimensions, but performs a full exact diagonalization if the effective Hamiltonian has small dimensions.
  The threshold introduced is the new DMRG parameter ``'max_N_for_ED'``.
- Derive the following classes (and their subclasses) from the new :class:`~tenpy.tools.hdf5_io.Hdf5Exportable`
  to support saving to HDF5:
  - :class:`~tenpy.networks.site.Site`
  - :class:`~tenpy.networks.terms.Terms`
  - :class:`~tenpy.networks.terms.OnsiteTerms`
  - :class:`~tenpy.networks.terms.CouplingTerms`
  - :class:`~tenpy.models.model.Model`, i.e., all model classes.
- By default, for an usual MPO define `IdL` and `IdR` on all bonds. This can generate "dead ends" in the MPO graph of
  finite systems, but it is useful for the `make_WI`/`make_WII` for MPO-exponentiation.


Fixed
^^^^^
- Adjust the default DMRG parameter `min_sweeps` if `chi_list` is set.
- Avoid some unnecessary transpositions in MPO environments for MPS sweeps (e.g. in DMRG).
- :class:`~tenpy.linalg.charges.LegPipe` did not initialize ``self.bunched`` correctly.
- :issue:`98`: Error of calling `psi.canonical_form()` directly after disabling the DMRG mixer.
- :func:`~tenpy.linalg.np_conserved.svd` with ``full_matrices=True`` gave wrong charges.
- wrong pairs for the `fifth_nearest_neighbors` of the :class:`~tenpy.models.lattice.Honeycomb`.
- Continue in :func:`tenpy.algorithms.dmrg.full_diag_effH` with a warning instaed of raising an Error,
  if the effective Hamltonian is zero.
- :meth:`~tenpy.networks.mps.MPS.correlation_length`: check for hermitian Flag might have raised and Error with new numpy warnings
- :meth:`~tenpy.networks.mps.MPS.correlation_function` did not respect argument ``str_on_first=False``.
- :meth:`tenpy.networks.mps.MPS.get_op` worked unexpected for infinite `bc` with incomensurate ``self.L`` and ``len(op_list)``.

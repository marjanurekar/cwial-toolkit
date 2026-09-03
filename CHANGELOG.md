# Changelog

Format follows Keep a Changelog. Versions follow semantic versioning.

## [0.3.0] - 2026-09-03

Register integrity, licensing, and alignment with the published VFRB record.

### Changed, breaking for existing databases

- `sources` now carries `UNIQUE(proposition_id, source_name)` and
  `add_source()` uses `INSERT OR IGNORE`. Re-running a seeding script no
  longer inflates the source count, so the three-source check reports
  evidential sufficiency rather than how often a script was executed.
  Databases created before 0.3.0 lack the constraint. The `VFRB` constructor
  detects this and warns; rebuild from a fresh file.
- `add_proposition()` writes `entry_date` once. A later call updates
  `last_verified` and `expiry_date` and preserves the original entry date.
- `InstrumentRegistry.register()` rejects a duplicate `(name, version)` and
  returns False instead of appending a second row.
- `register()` requires an explicit `calibration_date` when `itype` is
  `"survey"`. For a survey that is the fieldwork date. The previous default
  of today recorded a false fact about the instrument. Survey rows carry a
  non-date marker for `next_calibration_due`, because a completed wave
  cannot be re-fielded, and `due_for_calibration()` skips them.

### Changed

- `UncertaintyBudget.critical_value()` no longer describes itself as the
  distinguishability criterion, and `summary()` no longer prints
  "distinguishable from null" against it. The package reports one verdict,
  `distinguishable_from_zero`, at `|BDI| > U = 2 u_c`. The Currie critical
  value at 1.645 u_c is quoted alongside it as a capability of the procedure.
- `report.py` takes a `laboratory` argument instead of hardcoding CWIAL No. 1,
  labels the truth value as a truth value rather than as a numeric true
  value, prints the numeric value separately where one exists, and states
  that the measuring instrument is not counted among the sources.
- The library no longer prints on every call. `UncertaintyBudget`, `VFRB`,
  `InstrumentRegistry` and `generate_report` take a `verbose` flag, and
  `compute_bdi()` passes it through.

### Fixed, alignment with the published VFRB record (DOI 10.5281/zenodo.22277183)

- `brexit_350m_example.py` entered `numeric_value=190` with
  `numeric_uncertainty=10`, attributed to the UK Statistics Authority. The
  Authority issued no net estimate. The entry now records the gross figure of
  325 and the note states the accounting bases and that no net estimate is
  attributed to the Authority.
- The example counted the KCL / Ipsos MORI survey as a third source for the
  truth value. The survey is the measuring instrument. It has been removed
  from the source register, the entry stands at two sources, and the
  shortfall is declared rather than padded.
- The claim-aware base is 1474, derived as 2200 x 0.67, matching the
  published instrument record. The example previously used 1467.
- The u_B2 description read "half-width 0.10 at ~95%", which implies a
  divisor of 1.96 and a value of 0.051, while the value entered was 0.050.
  It now reads "at k=2".

### Added

- `LICENSE` (MIT). The README previously carried a sentence in place of a
  licence, which left the default position at all rights reserved.
- `CITATION.cff` and `.zenodo.json`.
- Scope note in `simulate.py`: agents are surveyed independently, so the
  simulated data carries D_eff = 1 and the budget under test is u_c ~ 0.075,
  not the 0.076 declared in the reports. The recovery check validates the
  estimator and the propagation under simple random sampling and says nothing
  about the design effect correction.
- Scope note in `ncs_validation.py`: the reproducibility component is
  estimated from three conditions, carries large uncertainty of its own, and
  is biased low because `pstdev` divides by n.
- README restores the guidance on derived bases, on not counting the
  instrument as a source, and on stating the divisor.

## [0.2.0]

Alignment with the revised Papers 2 and 3. See the README section for detail.

# CWIAL Starter Kit
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22288415.svg)](https://doi.org/10.5281/zenodo.22288415)

A minimal, ISO/IEC 17025-aligned toolkit for running a small Cognitive Warfare
Information Analysis Laboratory (CWIAL), implementing the Cognitive Warfare
Information Metrology Framework (CWIMF) described in:

- **Paper 1** (IcETRAN 2026): *Ten Metrological Principles for Understanding and
  Countering Cognitive Warfare*
- **Paper 2** (Kongres metrologa 2026, under review): *A Formal Measurement Architecture
  for CWIMF, Based on VIM, GUM, and ISO/IEC 17025*
- **Paper 3** (Measurement, Elsevier, under review): the CWIAL laboratory
  measurement paper, in which the detection quantities, the difference
  operators, and the verdict vocabulary used by this toolkit are defined

No external dependencies. Pure Python 3.8+, SQLite (stdlib), CSV (stdlib).
See "Verification" below for what the example scripts do and do not establish.

### Changes in 0.3.0 (register integrity)

The register now enforces two properties that were previously left to the
caller, both of which affected the audit trail:

- A source is unique per proposition. Previously, re-running a seeding script
  appended the same sources again, so the three-source check counted how often
  a script had been run rather than how much evidence was on file. Databases
  created before 0.3.0 lack the constraint; the constructor detects this and
  warns. Rebuild from a fresh file.
- `entry_date` is written once. A later call updates `last_verified` and
  leaves the original entry date intact.
- The instrument registry rejects duplicate `(name, version)` rows, and
  requires an explicit `calibration_date` for a survey instrument. For a
  survey that date is the fieldwork date; defaulting to today recorded a
  false fact about the instrument. A completed wave cannot be re-fielded and
  carries a non-date marker for its next calibration.
- `critical_value()` no longer describes itself as the distinguishability
  criterion. This package reports one verdict, `distinguishable_from_zero`,
  at `|BDI| > U`; the Currie critical value is quoted alongside it as a
  capability of the procedure.
- The library no longer prints on every call. Pass `verbose=True` where you
  want the running commentary.
- MIT licence added. See `LICENSE`.

### Changes in 0.2.0 (alignment with revised Papers 2 and 3)

The measurement vocabulary was corrected to match the revised papers:

- A single measurement now reports one verdict, `distinguishable_from_zero`
  (`|BDI| > U`). The former `passes_response_threshold` flag and the
  "RESPONSE JUSTIFIED" / "WITHIN NOISE FLOOR" strings, which conflated
  distinguishability with true-value estimation and with the decision to
  act, were removed.
- The detection quantities (critical value, MDD, and the new response
  threshold 3.645*u_c) are reported as instrument-capability statements
  evaluated at the null, with an explicit note that for a verified-false
  proposition the null is not physically realisable, so substantive claims
  rest on differences.
- `detection_threshold()` is renamed `critical_value()` (the old name is
  kept as an alias) to match Currie 1968 / ISO 11843-1.
- `compute_cav()` can now propagate endpoint uncertainty through a declared
  cross-wave correlation rather than assuming independence or exact
  cancellation.
- The synthetic recovery study is described as validating the estimator and
  propagation only, not the reference or the design effect. References to a
  "digital calibration standard" and to the VFRB as a "certified reference
  material" were softened to "synthetic reference" and "reference standard
  analogous to a CRM".

## Quick start

```bash
cd cwial-starter-kit
python examples/brexit_350m_example.py
python examples/simulation_validation.py
```

This reproduces the Paper 3 worked example end-to-end and confirms your
installation is correct: **BDI = +0.420 +/- 0.153 (k=2, ~95% coverage)**,
u_c = 0.076. A full ISO/IEC 17025-style report is written to `reports/`.
(The interval is a coverage interval, not a confidence interval in the
frequentist sense; the distinction is kept throughout.)

## What's in the box

| Module | Implements | ISO/IEC 17025 clause |
|---|---|---|
| `cwial/vfrb.py` | Verified Factual Reference Base | 6.5 (traceability) |
| `cwial/uncertainty.py` | GUM Type A / Type B budget engine | 7.6 (uncertainty) |
| `cwial/measurands.py` | BDI, CAV computation | 7.2 (method) |
| `cwial/instruments.py` | Instrument registry & calibration tracking | 6.4 (equipment) |
| `cwial/report.py` | Cognitive threat report generator | 7.8 (reporting) |
| `cwial/simulate.py` | Monte Carlo: synthetic attack scenarios & detection power curves | 7.2 (method validation) |
| `cwial/ncs_validation.py` | Metrological characterization of an LLM/classifier as an NCS instrument | 7.2 / 7.6 (validation, uncertainty) |

## Verification

The three example scripts run end-to-end with zero external dependencies:
- `brexit_350m_example.py` reproduces the Paper 3 worked example's BDI, u_c,
  U, and MDD to within rounding tolerance.
- `simulation_validation.py` confirms recovery coverage, the null-case
  false-detection rate, and the empirical detection capability.
- `ncs_instrument_validation.py` recovers injected variance components and
  biases on synthetic instrument data.
What these establish is internal consistency -- that the estimators and the
propagation are correct. They do not validate the reference base or the
design-effect assumption; those require the external work described in
Paper 3, Section 8.

## Data provenance note

`examples/brexit_350m_example.py` reproduces Paper 3 Section 6:
BDI = +0.42 +/- 0.153 (k=2), u_c = 0.076, MDD (capability) = 0.251,
|BDI|/U = 2.75. The last ratio says the reading is distinguishable from
zero by 2.75 expanded uncertainties; it is a scale, not a verdict that a
response is warranted.

Four points matter for anyone adapting it:

1. **Population.** The 42% figure is from the *Brexit Misperceptions* survey
   (Policy Institute at King's College London / Ipsos MORI / UK in a Changing
   Europe, Oct 2018). It is 42% of respondents **who had heard the claim**
   (67% of >2,200 GB adults 18-75), so the target population is the
   claim-aware subpopulation, not all UK adults.
2. **Derived bases are not measured bases.** The claim-aware base 1,474 is
   computed as 2,200 x 0.67. No such base is published directly. Do not
   write it to four significant figures as though it were measured.
3. **u_B1 is classification risk, not numeric range.** GBP350M is a gross
   figure taken before the rebate. For 2016/17 HM Treasury reports gross
   ~GBP325M/week, ~GBP235M/week after the rebate, and ~GBP156M/week net of
   public-sector receipts. The UK Statistics Authority found the use of the
   figure misleading; it issued no net estimate of its own, and none is
   attributed to it here. For a binary proposition none of these ranges
   propagate: the claim is false on every basis. Only the probability that
   the truth-value assignment is itself wrong propagates.
4. **Do not count your instrument as a source for your reference.** The VFRB
   source register holds sources for the *truth value* only. The survey is
   the instrument and belongs in the instrument registry. Keeping it out of
   the Brexit entry drops that entry below the three-source minimum, and the
   example declares the shortfall rather than padding the count.

Detection capability follows Currie (1968) / ISO 11843-1: the critical value
is 1.645*u_c and the minimum detectable displacement 3.29*u_c, with the
response threshold (95% power under |BDI| > 2u_c) at 3.645*u_c. These are
properties of the procedure at the null and characterise what the instrument
can resolve; they are not thresholds an individual output "passes". For a
verified-false proposition the null is not physically realisable, so they are
reported for scale and substantive claims rest on differences. A single
measurement supports one verdict: whether |BDI| > U, i.e. whether the reading
is distinguishable from zero. The toolkit's former `passes_response_threshold`
flag and its "RESPONSE JUSTIFIED" / "WITHIN NOISE FLOOR" strings conflated
distinguishability, true-value estimation, and the decision to act, and have
been replaced accordingly.

## Monte Carlo simulation module

`cwial/simulate.py` implements the two core MCM applications (Phase 1 of
the CWIMF validation roadmap):

1. **Synthetic recovery** -- an agent population with a known true BDI
   trajectory acts as a *synthetic reference* (analogous to, not identical
   with, a certified reference material: it is constructed, not produced
   under ISO 17034). Run `validate_recovery()` to confirm the pipeline
   recovers the constructed truth at the claimed k=2 coverage. This checks
   the estimator and the propagation only: a population built to a chosen
   design effect returns that design effect, which is internal consistency,
   not evidence about any real survey (Paper 3, Section 8.4). Typical output:
   coverage ~0.95 over 500 trials, empirical error sd ~ declared u_c.
2. **Detection power curves** -- `power_curve()` maps P(detect) against
   true displacement, yielding the instrument's empirical minimum
   detectable displacement. Note: under the *response* criterion
   |BDI| > U = 2u_c the 95%-power point sits near 0.28-0.30, above the
   Currie approximation 3.29*u0 ~ 0.25, which assumes the weaker
   detection threshold 1.645*u0 -- the simulation quantifies exactly
   this difference between detecting and acting.

Both run in seconds with zero dependencies. Extend them for SPC run-length
studies, survey-cadence design, and adversarial-adaptation games (see the
research roadmap).

## Starting your own case study (week 1 checklist)

1. Pick ONE narrow proposition in your chosen domain -- something with a
   clear true value and existing public polling data.
2. `vfrb.add_proposition(...)` -- enter it with at least 3 independent
   sources (`vfrb.add_source(...)`). If you cannot reach three, declare the
   shortfall. Do not count the survey you are measuring with.
3. Pull real survey data (see "Data sources" below) and compute Type A
   uncertainty from the actual sample proportion and size. Check whether the
   item was on a split ballot -- the item base is often not the wave n.
4. Estimate your five Type B components as honestly as you can -- even
   rough expert-judgment estimates are valid Type B evaluations per GUM.
   State the divisor you used, not just the result: "half-width 0.10 at
   ~95%" implies 1.96, while "half-width 0.10 at k=2" implies 2, and a
   referee will check which one your number reflects. Document your
   reasoning in the `notes` field.
5. Run `compute_bdi(...)`, inspect the budget, generate the report.
6. Commit the VFRB database, instrument registry, and report to your
   lab's git repo. This *is* your audit trail -- keep it from day one.

## Free real-world data sources to seed your VFRB and reconstruct BDI history

- **British Election Study** (bes.ac.uk) -- free microdata, UK attitudes
- **European Social Survey** (europeansocialsurvey.org) -- free, EU-wide
- **Eurobarometer** (europa.eu) -- free, EU trust/attitude surveys
- **Pew Research Center** (pewresearch.org) -- free US/international datasets
- **General Social Survey** (gss.norc.org) -- free, long-running US survey
- **EUvsDisinfo** (euvsdisinfo.eu) -- curated disinformation case database,
  excellent for VFRB seeding and historical BDI reconstruction
- **GDELT Project** (gdeltproject.org) -- free global news/media database,
  useful for NCS corpora and CAV time-series
- **MediaCloud** (mediacloud.org) -- narrative spread tracking across outlets
- **Fact-checking archives** -- Full Fact, PolitiFact, AFP Fact Check, Snopes

## Extending the toolkit (tasks for new team members)

- **VFRB curator**: expand `vfrb.py` usage -- build out 20-50 entries in
  your chosen domain with rigorous source documentation.
- **NLP/instrument engineer**: replace `compute_ncs()` stub in
  `measurands.py` with a real calibrated classifier; extend
  `instruments.py` with validation-run tracking.
- **Survey methodologist**: harden `type_a_uncertainty()` with proper
  design-effect calculations for your actual sampling designs.
- **Adversarial adaptation researcher**: this is the least-developed part
  of CWIMF (u_B5 in the uncertainty budget) -- a genuinely open research
  problem, good for a dedicated sub-project or thesis.

## Upgrade path

This toolkit is deliberately minimal so it is easy to outgrow correctly:
- Swap SQLite for PostgreSQL when the VFRB grows past a few thousand entries.
- Swap the CSV instrument registry for a proper database once you have more
  than a handful of instruments.
- Add a real NLP pipeline behind `compute_ncs()` when ready.
- When ready for formal accreditation, this toolkit's audit trail (VFRB
  history, instrument registry, generated reports) becomes your evidence
  base for an ISO/IEC 17025 application -- nothing needs to be rebuilt,
  only formalized.

## Citation

If you use this toolkit, cite the archived release rather than the repository.
`CITATION.cff` carries the machine-readable form and GitHub renders it as a
"Cite this repository" button.

## License

MIT. See `LICENSE` for the full text.

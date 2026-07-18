# CWIAL Starter Kit

A minimal, ISO/IEC 17025-aligned toolkit for running a small Cognitive Warfare
Information Analysis Laboratory (CWIAL), implementing the Cognitive Warfare
Information Metrology Framework (CWIMF) described in:

- **Paper 1**: *Ten Metrological Principles for Understanding and Countering Cognitive Warfare*
- **Paper 3**: *CWIMF -- A Formal Measurement Architecture Based on VIM, GUM, and ISO/IEC 17025*

No external dependencies. Pure Python 3.8+, SQLite (stdlib), CSV (stdlib).
Tested and confirmed working -- see "Verification" below.

## Quick start

```bash
cd cwial-starter-kit
python examples/brexit_350m_example.py
python examples/simulation_validation.py
```

This reproduces the Paper 3 worked example end-to-end and confirms your
installation is correct: **BDI = +0.420 +/- 0.149 (k=2, 95% confidence)**,
matching the published paper exactly. A full ISO/IEC 17025-style report
is written to `reports/`.

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

This toolkit was tested end-to-end before packaging:
- The Brexit worked example reproduces Paper 3B's published BDI, u_c, U, and
  MDD values to within rounding tolerance.
- VFRB expiry checking, instrument overdue-calibration checking, CAV
  computation, and the NCS stub were all independently tested.
- All modules import and run cleanly with zero external dependencies.

## Data provenance note

`examples/brexit_350m_example.py` reproduces Paper 3B Section 6 exactly:
BDI = +0.42 +/- 0.153 (k=2), u_c = 0.076, MDD = 0.251, |BDI|/U = 2.75.

Two points matter for anyone adapting it:

1. **Population.** The 42% figure is from the *Brexit Misperceptions* survey
   (Policy Institute at King's College London / Ipsos MORI / UK in a Changing
   Europe, Oct 2018). It is 42% of respondents **who had heard the claim**
   (~two-thirds of >2,200 GB adults 18-75), so the target population is the
   claim-aware subpopulation, n ~ 1,467 -- not all UK adults.
2. **u_B1 is classification risk, not numeric range.** For a binary
   proposition the +/-GBP10M uncertainty on the net contribution does not
   propagate: the claim is false whether the figure is 180 or 200. Only the
   probability that the truth-value assignment is itself wrong propagates.

Detection capability follows Currie (1968) / ISO 11843-1: the detection
threshold is 1.645*u_c and the minimum detectable displacement 3.29*u_c.
The earlier `3*u_c` "limit of detection" has been removed.

## Monte Carlo simulation module

`cwial/simulate.py` implements the two core MCM applications (Phase 1 of
the CWIMF validation roadmap):

1. **Synthetic attack scenarios** -- an agent population with a known true
   BDI trajectory acts as a *digital calibration standard*. Run
   `validate_recovery()` to confirm the full pipeline (sampling + bias
   sources + uncertainty budget) recovers the known truth at the claimed
   k=2 coverage. Verified output: coverage 0.948 over 500 trials,
   empirical error sd 0.076 = declared u_c.
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
   sources (`vfrb.add_source(...)`), following the Brexit example.
3. Pull real survey data (see "Data sources" below) and compute Type A
   uncertainty from the actual sample proportion and size.
4. Estimate your five Type B components as honestly as you can -- even
   rough expert-judgment estimates are valid Type B evaluations per GUM.
   Document your reasoning in the `notes` field.
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

## License

Use freely for your own CWIAL research and development.

# CWIAL Starter Kit

**v0.2.0** — realigned with the revised CWIMF papers. See "Migrating from
v0.1.0" below; the response-threshold API changed and the old one was wrong.

A minimal, ISO/IEC 17025-aligned toolkit for running a small Cognitive Warfare
Information Analysis Laboratory (CWIAL), implementing the Cognitive Warfare
Information Metrology Framework (CWIMF) described in:

- (IcETRAN 2026): *Ten Metrological Principles for Understanding and
  Countering Cognitive Warfare*

No external dependencies. Pure Python 3.8+, SQLite (stdlib), CSV (stdlib).

## Quick start

```bash
cd cwial-starter-kit
python examples/brexit_350m_example.py
python examples/simulation_validation.py
```

A full ISO/IEC 17025-style report is written to `reports/`.

## What's in the box

| Module | Implements | ISO/IEC 17025 clause |
|--|--|--|
| `cwial/vfrb.py` | Verified Factual Reference Base | 6.5 (traceability) |
| `cwial/uncertainty.py` | GUM Type A / Type B budget engine | 7.6 (uncertainty) |
| `cwial/measurands.py` | BDI, CAV computation | 7.2 (method) |
| `cwial/instruments.py` | Instrument registry & calibration tracking | 6.4 (equipment) |
| `cwial/report.py` | Cognitive threat report generator | 7.8 (reporting) |
| `cwial/simulate.py` | Monte Carlo: synthetic attack scenarios & power curves | 7.2 (method validation) |
| `cwial/ncs_validation.py` | Metrological characterization of an LLM/classifier as an NCS instrument | 7.2 / 7.6 (validation, uncertainty) |

## Migrating from v0.1.0

**The v0.1.0 response-threshold logic was wrong and produced an overstated
headline.** It compared `|BDI|` against `U = 2·u_c`, called `U` the response
threshold, and printed `RESPONSE JUSTIFIED`. On the Brexit example that gave
"2.8× the response threshold" when the correct figure is 1.51×.

| v0.1.0 | v0.2.0 | why |
|--|--|--|
| `BDIResult.passes_response_threshold` | `distinguishable_from_zero` and `exceeds_response_threshold` | one flag conflated two different comparisons |
| `"RESPONSE JUSTIFIED"` verdict string | capability statements, no verdict | the null it decided against cannot be prepared |
| `UncertaintyBudget.detection_threshold()` | `UncertaintyBudget.critical_value()` | Currie/ISO 11843-1 terminology, standardised across the programme |
| — | `UncertaintyBudget.response_threshold()` | 3.645·u_c, new |
| "digital calibration standard", "certified reference material" | "reference standard analogous to a CRM", with the ISO 17034 caveat | nothing here is a certified reference material |

Three thresholds, three different jobs:

- **Critical value, 1.645·u_c** — above this, a reading is distinguishable
  from what the procedure returns at the null.
- **Minimum detectable displacement, 3.29·u_c** — Currie's L_D, quoted in
  Currie's own convention for comparability with the detection-capability
  literature. It is paired with the critical value 1.645·u_0, *not* with
  this laboratory's decision criterion.
- **Response threshold, 3.645·u_c** — the 95%-power point under the
  criterion `|BDI| > U`. Against that stricter criterion, 3.29·u_c buys only
  90% power. This is the number to divide by when asking how far above the
  actionable threshold a displacement sits.

## The null is not realisable — read this before reporting a decision

For a verified-false proposition, the null state is a population holding the
belief at zero prevalence. No such population has ever existed, so u_0 cannot
be measured and is only approximated by u_c. Everything in the capability
block is therefore a statement about **what the instrument can resolve**, not
a verdict on the world. The toolkit will not print one.

Where a decision is genuinely required, refer it to a **difference** — the
same instrument, on the same population, at two times — because a null of no
change *is* attainable. And when you difference two measurements, do not
assume shared Type B components cancel exactly: they are correlated by
construction. Declare a correlation model and propagate it.

## Data provenance note

`examples/brexit_350m_example.py` reproduces Paper 3B Section 6:
BDI = +0.42 ± 0.153 (k=2), u_c = 0.076, L_C = 0.126, MDD = 0.251,
response threshold = 0.278, |BDI|/response threshold = 1.51.

Four points matter for anyone adapting it:

1. **Population.** The 42% figure is from the *Brexit Misperceptions* survey
   (Policy Institute at KCL / Ipsos MORI / UK in a Changing Europe, Oct 2018).
   It is 42% of respondents **who had heard the claim** (67% of >2,200 GB
   adults 18-75), so the target population is the claim-aware subpopulation.
2. **Derived bases are not measured bases.** The claim-aware base ~1,470 is
   computed from published percentages; no such base is published directly.
   Do not write it to four significant figures.
3. **u_B1 is classification risk, not numeric range.** For a binary
   proposition the spread between £325M gross, £235M after rebate and £156M
   net does not propagate: the claim is false on every basis. Only the
   probability that the truth-value assignment is itself wrong propagates.
4. **Do not count your instrument as a source for your reference.** The VFRB
   source register holds sources for the *truth value* only. The survey is
   the instrument and belongs in the instrument registry. Removing it from
   the Brexit entry drops it below the three-source minimum — the example
   declares that shortfall rather than padding the count.

Note also that `D_eff` must be declared per sampling design. Carrying one
study's value across to another because it is already in your code is not a
Type B evaluation.

## Monte Carlo simulation module

`cwial/simulate.py` implements the two core MCM applications (Phase 1 of
the CWIMF validation roadmap):

1. **Synthetic attack scenarios** — an agent population with a known true
   BDI trajectory acts as a *reference standard analogous to a CRM*. The
   analogy is bounded: no ISO 17034 issuing process stands behind it, and its
   "certified value" is a property of the model, not of any real population.
   Run `validate_recovery()` to confirm the full pipeline recovers the known
   truth at the claimed k=2 coverage. Verified output: coverage 0.948 over
   500 trials, empirical error sd 0.076 = declared u_c.
2. **Detection power curves** — `power_curve()` maps P(detect) against true
   displacement. Verified output: the 95%-power point lands at 0.30, next to
   the response threshold 3.645·u_c = 0.278 and clearly above the Currie MDD
   0.251. That gap is the point of the exercise: it is the difference between
   detecting and acting, and v0.1.0 hid it by comparing against the wrong
   constant.

## Starting your own case study (week 1 checklist)

1. Pick ONE narrow proposition in your chosen domain — something with a
   clear true value and existing public polling data.
2. `vfrb.add_proposition(...)` — enter it with at least 3 independent
   sources (`vfrb.add_source(...)`). If you cannot reach three, declare the
   shortfall. Do not count the survey you are measuring with.
3. Pull real survey data (see "Data sources" below) and compute Type A
   uncertainty from the actual sample proportion and size. Check whether the
   item was on a split ballot — the item base is often not the wave n.
4. Estimate your five Type B components as honestly as you can — even
   rough expert-judgment estimates are valid Type B evaluations per GUM.
   State the divisor you used, not just the result: "half-width 0.10 at
   ~95%" implies 1.96, while "half-width 0.10 at k=2" implies 2, and a
   referee will check which one your number reflects.
5. Run `compute_bdi(...)`, inspect the budget, generate the report. Read the
   capability block as capability, not as permission.
6. Commit the VFRB database, instrument registry, and report to your
   lab's git repo. This *is* your audit trail — keep it from day one.

## Free real-world data sources to seed your VFRB and reconstruct BDI history

- **British Election Study** (bes.ac.uk) — free microdata, UK attitudes
- **European Social Survey** (europeansocialsurvey.org) — free, EU-wide
- **Eurobarometer** (europa.eu) — free, EU trust/attitude surveys
- **GESIS** (gesis.org) — Eurobarometer codebooks and microdata; the place
  to check item wording, split ballots and list context between waves
- **Pew Research Center** (pewresearch.org) — free US/international datasets
- **General Social Survey** (gss.norc.org) — free, long-running US survey
- **EUvsDisinfo** (euvsdisinfo.eu) — curated disinformation case database
- **GDELT Project** (gdeltproject.org) — free global news/media database
- **MediaCloud** (mediacloud.org) — narrative spread tracking across outlets
- **Fact-checking archives** — Full Fact, PolitiFact, AFP Fact Check, Snopes

## Extending the toolkit (tasks for new team members)

- **VFRB curator**: build out 20-50 entries in your chosen domain with
  rigorous source documentation and honest independence assessments.
- **NLP/instrument engineer**: replace `compute_ncs()` stub in
  `measurands.py` with a real calibrated classifier; extend
  `instruments.py` with validation-run tracking.
- **Survey methodologist**: harden `type_a_uncertainty()` with proper
  design-effect calculations for your actual sampling designs.
- **Difference propagation**: implement the correlation model for ΔBDI and
  CAV so shared Type B components neither cancel exactly nor add in full.
- **Adversarial adaptation researcher**: the least-developed part of CWIMF
  (u_B5) — a genuinely open problem, good for a dedicated sub-project.

## Upgrade path

This toolkit is deliberately minimal so it is easy to outgrow correctly:
- Swap SQLite for PostgreSQL when the VFRB grows past a few thousand entries.
- Swap the CSV instrument registry for a proper database once you have more
  than a handful of instruments.
- Add a real NLP pipeline behind `compute_ncs()` when ready.
- When ready for formal accreditation, this toolkit's audit trail (VFRB
  history, instrument registry, generated reports) becomes your evidence
  base for an ISO/IEC 17025 application — nothing needs to be rebuilt,
  only formalized.

## License

Use freely for your own CWIAL research and development.

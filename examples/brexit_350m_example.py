"""
Reproduces the worked example from Paper 3, Section 6.

Run this first to check that your installation reproduces the published
numbers:  BDI = +0.42 +/- 0.15 (k=2, ~95% coverage), MDD ~ 0.25.

DATA PROVENANCE
---------------
The 42% belief figure comes from the 'Brexit Misperceptions' survey by the
Policy Institute at King's College London, with Ipsos MORI and UK in a
Changing Europe, published October 2018 (n > 2,200 GB adults aged 18-75).
Approximately two-thirds of respondents had heard the claim, and 42% of
THOSE AWARE believed it true. The target population P is therefore the
claim-aware subpopulation (n ~ 1,467), not all UK adults -- this matters,
and getting it wrong is the kind of error the framework exists to catch.

Usage:  python examples/brexit_350m_example.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cwial.vfrb import VFRB
from cwial.instruments import InstrumentRegistry
from cwial.measurands import compute_bdi
from cwial.report import generate_report

PROP_ID = "UK-EU-350M-2016"

# Claim-aware subsample: ~two-thirds of the >2,200 respondents
N_AWARE = 1467
P_BELIEVE = 0.42
D_EFF = 1.8          # DECLARED assumption for a quota-controlled online panel,
                     # not derived from the source study's design documentation


def main():
    # --- 1. Seed the VFRB entry ---
    vfrb = VFRB(db_path="data/vfrb.db")
    vfrb.add_proposition(
        prop_id=PROP_ID,
        text="The UK sends GBP 350 million per week to the European Union.",
        truth_value="FALSE",
        tier=2,
        maintainer="CWIAL No. 1",
        numeric_value=190,       # net contribution, GBP million/week
        numeric_uncertainty=10,  # +/- GBP 10M per UK Statistics Authority
        notes="Gross GBP350M excludes the UK rebate; net ~GBP190M per UK "
              "Statistics Authority, 27 May 2016. NOTE: for this BINARY "
              "proposition the +/-GBP10M numeric range does NOT propagate "
              "into the BDI budget -- the claim is false whether the net "
              "figure is 180 or 200. Only the risk that the truth-value "
              "assignment itself is wrong propagates, as u_B1 (Paper 3 "
              "Sec. 5.3)."
    )
    vfrb.add_source(PROP_ID, "UK Statistics Authority statement, 27 May 2016",
                    isrg_grade="I",
                    url="https://uksa.statisticsauthority.gov.uk/news/"
                        "uk-statistics-authority-statement-on-the-use-of-official-"
                        "statistics-on-contributions-to-the-european-union/")
    vfrb.add_source(PROP_ID, "HM Treasury EU contribution figures", isrg_grade="I")
    vfrb.add_source(PROP_ID,
                    "Policy Institute at King's College London / Ipsos MORI / "
                    "UK in a Changing Europe, 'Brexit Misperceptions', Oct 2018",
                    isrg_grade="II",
                    url="https://www.kcl.ac.uk/policy-institute/assets/"
                        "brexit-misperceptions.pdf")
    vfrb.source_count(PROP_ID)

    # --- 2. Register the instrument ---
    reg = InstrumentRegistry(path="data/instruments.csv")
    reg.register(
        name="KCL-IpsosMORI-Brexit-Misperceptions", version="2018-10",
        itype="survey",
        known_bias="Opt-in panel; residual demographic skew budgeted as u_B4",
        notes="n>2,200 GB adults 18-75; claim-aware subsample n~%d." % N_AWARE
    )

    # --- 3. Compute BDI with the Paper 3 GUM uncertainty budget ---
    # Each component is a zero-expectation correction term in the additive
    # measurement model of Paper 3 eq. 3, so all sensitivity coefficients
    # are unity and the combined uncertainty is an exact quadrature sum.
    type_b = {
        "u_B1_reference_classification": (
            0.030, "Tier-2 truth-classification risk (NOT numeric range)"),
        "u_B2_instrument_bias": (
            0.050, "Assumed framing shift, half-width 0.10 at ~95% (illustrative)"),
        "u_B3_temporal_mismatch": (
            0.026, "28 months campaign->measurement; +/-0.045 rect /sqrt(3)"),
        "u_B4_panel_representativeness": (
            0.035, "Opt-in panel skew; +/-0.061 rect /sqrt(3)"),
        "u_B5_adversarial_adaptation": (
            0.015, "Residual claim reuse; +/-0.037 triangular /sqrt(6)"),
    }

    result, budget = compute_bdi(
        proposition_id=PROP_ID,
        p_believe_false=P_BELIEVE,
        n=N_AWARE,
        design_effect=D_EFF,
        type_b_components=type_b,
    )

    print()
    print(budget.summary())
    print()
    print(result)
    print()

    # --- Checks against the published Paper 3 result ---
    assert abs(result.bdi - 0.42) < 0.001, "BDI mismatch vs published result"
    assert abs(result.u_c - 0.076) < 0.002, "u_c mismatch vs published result"
    assert abs(result.U - 0.153) < 0.004, "Expanded uncertainty mismatch"
    assert abs(result.mdd - 0.25) < 0.01, "MDD (capability) mismatch vs published result"
    print("[OK] Reproduced Paper 3: BDI = +0.42 +/- 0.15 (k=2), "
          "u_c = 0.076; instrument MDD (capability) = 0.25")
    # |BDI| > U establishes distinguishability from zero, and nothing more.
    # The ratio is a scale, not a verdict on actionability.
    print("[OK] |BDI| = %.2f exceeds U = %.2f -> distinguishable from zero "
          "(|BDI|/U = %.2f)."
          % (abs(result.bdi), result.U, abs(result.bdi)/result.U))
    print("     The observed |BDI| also lies above the instrument's response "
          "threshold (%.3f), i.e. outside the range where the instrument's "
          "capability would be in question; this is a statement of scale, not "
          "proof that the true displacement exceeds that threshold." 
          % result.response_threshold)

    # --- 4. ISO/IEC 17025 clause-7.8-style report ---
    vfrb_entry = vfrb.get_proposition(PROP_ID)
    generate_report(
        bdi_result=result,
        budget=budget,
        vfrb_entry=vfrb_entry,
        population="GB adults aged 18-75 who report awareness of the proposition",
        method=("Brexit Misperceptions survey (Policy Institute at KCL / "
                "Ipsos MORI / UK in a Changing Europe, Oct 2018); "
                "claim-aware subsample n=%d; belief prevalence referenced to "
                "aligned prevalence p0=0 per Paper 3 eq. 1; D_eff=%.1f "
                "declared, not measured." % (N_AWARE, D_EFF)),
        analyst="CWIAL No. 1 (starter kit demo)",
    )


if __name__ == "__main__":
    main()

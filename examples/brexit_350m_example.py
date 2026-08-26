"""
Reproduces the worked example from Paper 3B, Section 6.

Run this first to check that your installation reproduces the published
numbers:  BDI = +0.42 +/- 0.15 (k=2, ~95% coverage), u_c = 0.076,
L_C = 0.126, MDD = 0.251 (Currie convention), response threshold = 0.278.

DATA PROVENANCE
---------------
The 42% belief figure comes from the 'Brexit Misperceptions' survey by the
Policy Institute at King's College London, with Ipsos MORI and UK in a
Changing Europe, published October 2018 (n > 2,200 GB adults aged 18-75).
Two-thirds (67%) of respondents had heard the claim, and 42% of THOSE
AWARE believed it true. The target population P is therefore the
claim-aware subpopulation, not all UK adults -- this matters, and getting
it wrong is the kind of error the framework exists to catch.

The claim-aware base is DERIVED from published percentages (2200 x 0.67),
not published directly. It is written here as 1470 rather than a
spuriously precise figure, and the derivation is declared.

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

# Claim-aware subsample: 67% of the >2,200 respondents (derived)
N_AWARE = 1470
P_BELIEVE = 0.42
D_EFF = 1.8          # DECLARED assumption for a quota-controlled online panel,
                     # not derived from the source study's design documentation.
                     # Declare D_eff separately for every sampling design; do
                     # not carry one study's value across to another.


def main():
    # --- 1. Seed the VFRB entry ---
    vfrb = VFRB(db_path="data/vfrb.db")
    vfrb.add_proposition(
        prop_id=PROP_ID,
        text="The UK sends GBP 350 million per week to the European Union.",
        truth_value="FALSE",
        tier=2,
        maintainer="CWIAL No. 1",
        numeric_value=325,       # gross contribution, GBP million/week, 2016/17
        numeric_uncertainty=None,
        notes="GBP350M is a GROSS figure taken before the UK rebate. For "
              "2016/17 HM Treasury reports gross GBP16.9bn (~GBP325M/week); "
              "GBP12.2bn after the GBP4.8bn rebate (~GBP235M/week); and "
              "GBP8.1bn net of public-sector receipts (~GBP156M/week). The "
              "UK Statistics Authority concluded on 21 April 2016 that the "
              "figure's use was potentially misleading and stated on 27 May "
              "2016 that continued gross-for-net use was misleading; it "
              "issued NO net estimate of its own and none is attributed to "
              "it here. NOTE: for this BINARY proposition none of these "
              "numeric ranges propagate into the BDI budget -- the claim is "
              "false on every basis. Only the risk that the truth-value "
              "assignment itself is wrong propagates, as u_B1 (Paper 3B "
              "Sec. 5.3)."
    )
    # Sources for the TRUTH VALUE only. The survey is the instrument, not a
    # reference for V(F), and is registered below instead of counted here.
    vfrb.add_source(PROP_ID, "UK Statistics Authority statement, 27 May 2016",
                    isrg_grade="I",
                    url="https://uksa.statisticsauthority.gov.uk/news/"
                        "uk-statistics-authority-statement-on-the-use-of-official-"
                        "statistics-on-contributions-to-the-european-union/")
    vfrb.add_source(PROP_ID, "HM Treasury EU contribution figures, 2016/17",
                    isrg_grade="I")
    n_src = vfrb.source_count(PROP_ID)
    if n_src < 3:
        print("[VFRB] Shortfall DECLARED, not padded: the KCL/Ipsos MORI survey")
        print("       is the measuring instrument and is not counted as a source")
        print("       for V(F). Note also that the two sources above are not")
        print("       fully independent -- the Authority comments on Treasury")
        print("       and ONS figures.")

    # --- 2. Register the instrument ---
    reg = InstrumentRegistry(path="data/instruments.csv")
    reg.register(
        name="KCL-IpsosMORI-Brexit-Misperceptions", version="2018-10",
        itype="survey",
        known_bias="Opt-in panel; residual demographic skew budgeted as u_B4",
        notes="n>2,200 GB adults 18-75, online; claim-aware subsample n~%d "
              "(derived, 67%% of wave)." % N_AWARE
    )

    # --- 3. Compute BDI with the Paper 3B GUM uncertainty budget ---
    # Each component is a zero-expectation correction term in the additive
    # measurement model of Paper 3B eq. 3, so all sensitivity coefficients
    # are unity. The input quantities are treated as UNCORRELATED and the
    # covariance terms of GUM eq. 13 are dropped explicitly.
    type_b = {
        "u_B1_reference_classification": (
            0.030, "Tier-2 truth-classification risk (NOT numeric range)"),
        "u_B2_instrument_bias": (
            0.050, "Assumed framing shift, half-width 0.10 at k=2 (illustrative)"),
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

    # --- Checks against the published Paper 3B result ---
    assert abs(result.bdi - 0.42) < 0.001, "BDI mismatch vs published result"
    assert abs(result.u_c - 0.076) < 0.002, "u_c mismatch vs published result"
    assert abs(result.U - 0.153) < 0.004, "Expanded uncertainty mismatch"
    assert abs(result.mdd - 0.251) < 0.01, "MDD mismatch vs published result"
    assert abs(result.critical_value - 0.126) < 0.005, "L_C mismatch"
    assert abs(result.response_threshold - 0.278) < 0.006, "Response threshold mismatch"
    print("[OK] Reproduced Paper 3B: BDI = +0.42 +/- 0.15 (k=2), u_c = 0.076,")
    print("     L_C = 0.126, MDD = 0.251, response threshold = 0.278")
    print("[OK] |BDI|/response_threshold = %.2f"
          % (abs(result.bdi) / result.response_threshold))
    print("     NOTE: this ratio is against 3.645*u_c, NOT against U. Dividing")
    print("     by U and calling the result a multiple of the response")
    print("     threshold was the v0.1.0 error; it overstated the ratio by 1.8x.")

    # --- 4. ISO/IEC 17025 clause-7.8-style report ---
    vfrb_entry = vfrb.get_proposition(PROP_ID)
    generate_report(
        bdi_result=result,
        budget=budget,
        vfrb_entry=vfrb_entry,
        population="GB adults aged 18-75 who report awareness of the proposition",
        method=("Brexit Misperceptions survey (Policy Institute at KCL / "
                "Ipsos MORI / UK in a Changing Europe, Oct 2018); "
                "claim-aware subsample n~%d (derived); belief prevalence "
                "referenced to aligned prevalence p0=0 per Paper 3B eq. 1; "
                "D_eff=%.1f declared, not measured." % (N_AWARE, D_EFF)),
        analyst="CWIAL No. 1 (starter kit demo)",
    )


if __name__ == "__main__":
    main()

"""
Cognitive Threat Assessment Report generator.
Matches the ISO/IEC 17025 clause 7.8 structure from Paper 3, Table 2.
"""
import datetime
from pathlib import Path


REPORT_TEMPLATE = """\
============================================================
COGNITIVE THREAT ASSESSMENT REPORT
{laboratory}
============================================================
Report generated : {generated}
Analyst           : {analyst}

--- 1. MEASURAND IDENTIFICATION ---
Measurand         : {measurand}
Proposition ID    : {proposition_id}
Proposition text  : {proposition_text}

--- 2. TARGET POPULATION ---
{population}

--- 3. VFRB TRACEABILITY ---
Verified truth value       : {truth_value}
Verified numeric value     : {numeric_value}
VFRB tier                  : {tier}
Sources for the truth value: {n_sources} on file (the measuring instrument
                             is registered separately and is not counted here)

--- 4. MEASUREMENT METHOD ---
{method}

--- 5. RESULT ---
{result_line}

--- 6. UNCERTAINTY BUDGET ---
{budget}

--- 7. MEASUREMENT VERDICT AND CAPABILITY ---
{fitness_statement}

--- 8. TRACEABILITY STATEMENT ---
This measurement is traceable to VFRB proposition '{proposition_id}',
verified as of {vfrb_last_verified}, via the source chain documented
in the VFRB source register (see `vfrb.get_sources('{proposition_id}')`).
============================================================
"""


def generate_report(bdi_result, budget, vfrb_entry, measurand="BDI",
                     population="Not yet specified -- fill in target population.",
                     method="Survey-based Type A + documented Type B components.",
                     analyst="Unassigned", laboratory="CWIAL No. 1",
                     out_dir="reports", verbose=True):
    n_sources = len(vfrb_entry.get("sources", []))
    nv = vfrb_entry.get("numeric_value")
    nu = vfrb_entry.get("numeric_uncertainty")
    if nv is None:
        numeric_value = "none (binary proposition)"
    elif nu is None:
        numeric_value = f"{nv}"
    else:
        numeric_value = f"{nv} +/- {nu}"
    if bdi_result.distinguishable_from_zero:
        verdict = (
            "DISTINGUISHABLE FROM ZERO -- the measured displacement exceeds "
            "its expanded uncertainty, so the reading is not attributable to "
            "measurement noise at the stated coverage."
        )
    else:
        verdict = (
            "NOT DISTINGUISHABLE FROM ZERO -- the measured displacement does "
            "not exceed its expanded uncertainty; it cannot be separated from "
            "measurement noise at the stated coverage."
        )
    fitness_statement = (
        verdict + "\n" + bdi_result.capability_note() + "\n"
        "  Note: distinguishability is not a decision to act. Whether a "
        "displacement distinguishable from zero is also large enough to warrant "
        "a response is a separate, policy-level judgement that the measurement "
        "informs but does not make; and for a verified-false proposition the "
        "capability quantities above are properties of the procedure at a null "
        "that is not physically realisable (see method notes), reported for "
        "scale rather than as thresholds this output has passed."
    )

    text = REPORT_TEMPLATE.format(
        generated=datetime.datetime.now().isoformat(timespec="minutes"),
        analyst=analyst,
        laboratory=laboratory,
        measurand=measurand,
        proposition_id=vfrb_entry["id"],
        proposition_text=vfrb_entry["text"],
        population=population,
        truth_value=vfrb_entry["truth_value"],
        numeric_value=numeric_value,
        tier=vfrb_entry["tier"],
        n_sources=n_sources,
        method=method,
        result_line=str(bdi_result),
        budget=budget.summary(),
        fitness_statement=fitness_statement,
        vfrb_last_verified=vfrb_entry["last_verified"],
    )

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    fname = out_path / f"report_{vfrb_entry['id']}_{datetime.date.today().isoformat()}.txt"
    fname.write_text(text)
    if verbose:
        print(f"[Report] Written to {fname}")
    return text

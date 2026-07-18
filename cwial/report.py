"""
Cognitive Threat Assessment Report generator.
Matches the ISO/IEC 17025 clause 7.8 structure from Paper 3, Table 2.
"""
import datetime
from pathlib import Path


REPORT_TEMPLATE = """\
============================================================
COGNITIVE THREAT ASSESSMENT REPORT
CWIAL No. 1
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
Verified true value (V(F)) : {vf}
VFRB tier                  : {tier}
Sources                    : {n_sources} independent source(s) on file

--- 4. MEASUREMENT METHOD ---
{method}

--- 5. RESULT ---
{result_line}

--- 6. UNCERTAINTY BUDGET ---
{budget}

--- 7. FITNESS-FOR-PURPOSE DETERMINATION ---
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
                     analyst="Unassigned", out_dir="reports"):
    n_sources = len(vfrb_entry.get("sources", []))
    fitness_statement = (
        "PASS -- measured displacement exceeds expanded uncertainty; "
        "response consideration is metrologically justified."
        if bdi_result.passes_response_threshold else
        "MONITOR -- measured displacement within measurement noise floor; "
        "no response action metrologically justified at this time."
    )

    text = REPORT_TEMPLATE.format(
        generated=datetime.datetime.now().isoformat(timespec="minutes"),
        analyst=analyst,
        measurand=measurand,
        proposition_id=vfrb_entry["id"],
        proposition_text=vfrb_entry["text"],
        population=population,
        vf=vfrb_entry["truth_value"],
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
    print(f"[Report] Written to {fname}")
    return text

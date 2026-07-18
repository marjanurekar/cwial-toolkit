"""
Core CWIMF measurands: BDI and CAV (Paper 3, Section 4).
NCS and ISRG are provided as lightweight stubs for future expansion.
"""
from dataclasses import dataclass, field
from .uncertainty import UncertaintyBudget, type_a_uncertainty


@dataclass
class BDIResult:
    proposition_id: str
    bdi: float
    u_c: float
    U: float
    mdd: float
    k: int = 2
    passes_response_threshold: bool = field(init=False)

    def __post_init__(self):
        self.passes_response_threshold = abs(self.bdi) > self.U

    def __str__(self):
        verdict = "RESPONSE JUSTIFIED" if self.passes_response_threshold else "WITHIN NOISE FLOOR"
        return (f"BDI({self.proposition_id}) = {self.bdi:+.3f} +/- {self.U:.3f} "
                f"(k={self.k})  |  MDD={self.mdd:.3f}  |  {verdict}")


def compute_bdi(proposition_id, p_believe_false, n, design_effect=1.0,
                 sign=+1, type_b_components=None):
    """
    Full BDI computation with GUM uncertainty budget.

    proposition_id: VFRB proposition identifier
    p_believe_false: proportion of survey sample believing the false/displaced claim
    n: sample size
    design_effect: D_eff correction (default 1.0 = simple random sample)
    sign: +1 if believing the claim displaces belief toward FALSE (typical case),
          -1 if the framing is reversed
    type_b_components: dict of {name: (value, description)} - see uncertainty.py
    """
    s, u_a, u_a_corr = type_a_uncertainty(p_believe_false, n, design_effect)
    bdi_value = sign * p_believe_false  # simplified normalization per Paper 3 eq.1

    budget = UncertaintyBudget(u_a_corr, label=f"BDI[{proposition_id}]")
    if type_b_components:
        for name, (val, desc) in type_b_components.items():
            budget.add_type_b(name, val, desc)

    u_c = budget.combined_uncertainty()
    U = budget.expanded_uncertainty(k=2)
    mdd = budget.minimum_detectable_displacement()

    result = BDIResult(proposition_id=proposition_id, bdi=bdi_value, u_c=u_c, U=U, mdd=mdd)
    return result, budget


def compute_cav(bdi_t1, bdi_t2, delta_hours):
    """Cognitive Attack Velocity: rate of change of BDI (Paper 3, eq. 2)."""
    return (bdi_t2 - bdi_t1) / (delta_hours / 24.0)


# --- Stubs for future team members to build out (see README "next steps") ---

def compute_ncs(consistent_claims, total_claims):
    """
    Narrative Coherence Score stub.
    Replace with calibrated NLP classifier output (Paper 3, Section 4.2).
    """
    if total_claims == 0:
        raise ValueError("total_claims must be > 0")
    return consistent_claims / total_claims


ISRG_GRADES = ["I", "II", "III", "IV", "V"]  # I = highest reliability

"""
Core CWIMF measurands: BDI and CAV (Paper 3, Section 4).
NCS and ISRG are provided as lightweight stubs for future expansion.

v0.2.0 API CHANGE
-----------------
BDIResult.passes_response_threshold and the "RESPONSE JUSTIFIED" verdict
were removed. They compared |BDI| against U = 2*u_c and then called U the
response threshold, which conflated two different things and overstated
the instrument's standing. They are replaced by two explicitly-labelled
CAPABILITY flags:

  distinguishable_from_zero   |BDI| > 1.645*u_c   (critical value)
  exceeds_response_threshold  |BDI| > 3.645*u_c   (95% power at |BDI|>U)

Neither is a decision. For a verified-false proposition the zero-prevalence
null cannot be prepared, so u_0 is only approximated by u_c and these flags
must be reported as statements about what the procedure can resolve.
Substantive claims belong on differences, where a null of no change is
attainable.
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
    critical_value: float = 0.0
    response_threshold: float = 0.0
    k: int = 2
    distinguishable_from_zero: bool = field(init=False)
    exceeds_response_threshold: bool = field(init=False)

    def __post_init__(self):
        self.distinguishable_from_zero = abs(self.bdi) > self.critical_value
        self.exceeds_response_threshold = abs(self.bdi) > self.response_threshold

    def __str__(self):
        cap = ("ABOVE CRITICAL VALUE" if self.distinguishable_from_zero
               else "BELOW CRITICAL VALUE")
        rsp = ("above response threshold" if self.exceeds_response_threshold
               else "below response threshold")
        return (f"BDI({self.proposition_id}) = {self.bdi:+.3f} +/- {self.U:.3f} "
                f"(k={self.k})\n"
                f"  capability: L_C={self.critical_value:.3f}  "
                f"MDD={self.mdd:.3f}  resp={self.response_threshold:.3f}\n"
                f"  {cap}; {rsp}  [capability statements, not a decision:\n"
                f"   the zero-prevalence null is not physically realisable]")


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

    The additive model of Paper 3B eq. 3 gives unity sensitivity coefficients
    for every correction term, so the combination is an exact quadrature sum
    PROVIDED the input quantities are uncorrelated. Callers differencing two
    BDI values must not assume shared components cancel exactly.
    """
    s, u_a, u_a_corr = type_a_uncertainty(p_believe_false, n, design_effect)
    bdi_value = sign * p_believe_false  # simplified normalization per Paper 3 eq.1

    budget = UncertaintyBudget(u_a_corr, label=f"BDI[{proposition_id}]")
    if type_b_components:
        for name, (val, desc) in type_b_components.items():
            budget.add_type_b(name, val, desc)

    result = BDIResult(
        proposition_id=proposition_id,
        bdi=bdi_value,
        u_c=budget.combined_uncertainty(),
        U=budget.expanded_uncertainty(k=2),
        mdd=budget.minimum_detectable_displacement(),
        critical_value=budget.critical_value(),
        response_threshold=budget.response_threshold(),
    )
    return result, budget


def compute_cav(bdi_t1, bdi_t2, delta_hours):
    """
    Cognitive Attack Velocity: rate of change of BDI (Paper 3, eq. 2).

    The uncertainty on a CAV is NOT obtained by adding the two budgets in
    quadrature. Type B components shared between the two readings are
    correlated by construction; declare a correlation model and propagate it
    (Paper 3, Sec. 5.4). Assuming exact cancellation understates u(dBDI).
    """
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

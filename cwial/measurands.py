"""
Core CWIMF measurands: BDI and CAV (Paper 2, measurement architecture;
Paper 3, Section 4). NCS and ISRG are provided as lightweight stubs.

On verdict language (Paper 3, issues corrected in revision):

  A measurement establishes whether a displacement is DISTINGUISHABLE FROM
  ZERO at the stated coverage. It does not, by itself, establish that the
  TRUE displacement equals the observed one, nor that the displacement is
  large enough to act on. This module therefore reports:

    * distinguishable_from_zero : |BDI| > U. The reading is not noise.
    * observed vs capability    : the observed |BDI| is compared with the
      instrument's capability quantities (critical value, MDD, response
      threshold) FOR SCALE ONLY. Observing a value above the response
      threshold does not prove the true displacement lies above it; it
      shows the reading sits outside the range where the instrument's
      capability would be in question.

  The former field `passes_response_threshold` and the verdicts
  "RESPONSE JUSTIFIED" / "WITHIN NOISE FLOOR" conflated these and have been
  removed.
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
    critical_value: float = 0.0
    response_threshold: float = 0.0
    distinguishable_from_zero: bool = field(init=False)

    def __post_init__(self):
        # The only verdict a single measurement supports: is the reading
        # distinguishable from the null at the stated coverage?
        self.distinguishable_from_zero = abs(self.bdi) > self.U

    def __str__(self):
        verdict = ("distinguishable from zero"
                   if self.distinguishable_from_zero
                   else "not distinguishable from zero")
        return (f"BDI({self.proposition_id}) = {self.bdi:+.3f} +/- {self.U:.3f} "
                f"(k={self.k})  |  {verdict} at this coverage")

    def capability_note(self):
        """
        A scale comparison of the observed displacement against the
        instrument's capability quantities. Explicitly NOT a test the
        observation passes (see module docstring).
        """
        return (f"  observed |BDI| = {abs(self.bdi):.3f}; instrument capability "
                f"(properties of the procedure, shown for scale): "
                f"critical value {self.critical_value:.3f}, "
                f"MDD {self.mdd:.3f}, response threshold {self.response_threshold:.3f}")


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
    crit = budget.critical_value()
    resp = budget.response_threshold()

    result = BDIResult(proposition_id=proposition_id, bdi=bdi_value,
                       u_c=u_c, U=U, mdd=mdd,
                       critical_value=crit, response_threshold=resp)
    return result, budget


def compute_cav(bdi_t1, bdi_t2, delta_hours, u_bdi_t1=None, u_bdi_t2=None,
                rho=None):
    """
    Cognitive Attack Velocity: rate of change of BDI (Paper 2/3, eq. 2).

    Returns the point estimate. If the endpoint uncertainties are supplied,
    also returns the standard uncertainty of the rate, evaluated through the
    correlation between the two endpoint measurements rather than by assuming
    independence or exact cancellation.

    For a component present at both waves with correlation rho, its
    contribution to the variance of the DIFFERENCE is 2*u^2*(1 - rho):
    rho = 1 cancels exactly (a genuinely shared systematic), rho = 0 is full
    independence (a sample-specific term). Passing a single scalar `rho`
    applies it to the combined endpoint uncertainty as a simple first
    approximation; a component-by-component treatment (Paper 3, Section 6.4)
    is preferable when the budget is available.

    The name is inherited from the framework and denotes the rate of change
    of the BDI irrespective of cause. It implies no attribution to an
    adversary (Paper 3, Section 9.1).
    """
    years = delta_hours / 24.0 / 365.0
    rate = (bdi_t2 - bdi_t1) / years if years else float("nan")
    if u_bdi_t1 is None or u_bdi_t2 is None:
        return rate
    if rho is None:
        rho = 0.0
    # variance of the difference under a single shared correlation rho
    var_diff = u_bdi_t1**2 + u_bdi_t2**2 - 2 * rho * u_bdi_t1 * u_bdi_t2
    u_diff = max(var_diff, 0.0) ** 0.5
    u_rate = u_diff / years if years else float("nan")
    return rate, u_rate


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

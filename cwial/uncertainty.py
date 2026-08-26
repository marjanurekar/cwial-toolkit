"""
GUM-compliant uncertainty budget engine.
Implements Paper 3B, Section 5: Type A / Type B combination, expanded
uncertainty, and the capability-of-detection figures of Currie (1968) /
ISO 11843-1.

NOTE ON THE NULL (v0.2.0)
-------------------------
The capability figures below are properties of the MEASUREMENT PROCEDURE.
They are not, on their own, a decision. For a verified-false proposition
the null state -- a population holding the belief at zero prevalence --
cannot be physically prepared, so u_0 cannot be measured and is only
approximated by u_c. Capability figures computed here should therefore be
reported as capability statements. Substantive claims should rest on
DIFFERENCES, where a null of no change is attainable.
"""
import math


def type_a_uncertainty(p_hat, n, design_effect=1.0):
    """
    Type A standard uncertainty for a BDI estimate from a survey proportion.
    p_hat: observed proportion believing the false/displaced claim (0-1)
    n: sample size
    design_effect: D_eff correction for stratified/cluster sampling (>=1.0)
    Returns (s, u_A, u_A_corrected)
    """
    s = math.sqrt(p_hat * (1 - p_hat))
    u_a = s / math.sqrt(n)
    u_a_corrected = u_a * math.sqrt(design_effect)
    return s, u_a, u_a_corrected


class UncertaintyBudget:
    """
    Accumulates named Type B components and combines with a Type A component
    into a full GUM-compliant combined and expanded uncertainty.

    The combination is a quadrature sum. This is exact for a linear
    measurement model with UNCORRELATED input quantities. Both conditions
    must hold: state the linearity argument, and state explicitly that the
    covariance terms of GUM eq. 13 are dropped. Where Type B components are
    shared between two measurements being differenced, they are correlated
    by construction and must NOT be assumed to cancel exactly -- declare a
    correlation model instead (Paper 3, Sec. 5.4).
    """
    def __init__(self, u_a, label="BDI"):
        self.u_a = u_a
        self.label = label
        self.type_b = {}  # name -> (value, description)

    def add_type_b(self, name, value, description=""):
        self.type_b[name] = (value, description)
        print(f"[Uncertainty] Added Type B component '{name}' = {value:.4f}  ({description})")

    def combined_uncertainty(self):
        total_sq = self.u_a ** 2
        for name, (v, _) in self.type_b.items():
            total_sq += v ** 2
        return math.sqrt(total_sq)

    def expanded_uncertainty(self, k=2):
        return k * self.combined_uncertainty()

    def critical_value(self):
        """
        Critical value L_C (Currie 1968; ISO 11843-1): the value a reading
        must exceed to be distinguishable from a null result at a one-sided
        false-positive risk of 5%.

        Renamed from detection_threshold() in v0.2.0. Reported as a
        capability statement: u_0 is approximated by u_c because the null
        cannot be prepared for a single BDI. See the module docstring.
        """
        return 1.645 * self.combined_uncertainty()

    def minimum_detectable_displacement(self):
        """
        Currie MDD, L_D = 3.29 * u_0, with alpha = beta = 0.05 against the
        critical value 1.645 * u_0 (Paper 3B, eq. 8).

        Quoted in Currie's convention for comparability with the detection-
        capability literature. It is NOT the 95%-power point of this
        laboratory's decision criterion -- see response_threshold().
        """
        return 3.29 * self.combined_uncertainty()

    def response_threshold(self):
        """
        The 95%-power point under the criterion |BDI| > U = 2 u_c (new in
        v0.2.0).

        Against the stricter critical value U = 2 u_c, a displacement of
        3.29 u_c buys only Phi(3.29 - 2) = 90% power. The 95%-power point
        is 3.645 u_c. Quoting the Currie MDD as though it were the response
        threshold understates what the instrument needs by roughly 11%.
        """
        return 3.645 * self.combined_uncertainty()

    def summary(self):
        lines = [f"=== Uncertainty Budget: {self.label} ===",
                 f"Type A (u_A)              : {self.u_a:.4f}"]
        for name, (v, desc) in self.type_b.items():
            lines.append(f"Type B '{name}' (u_B)  : {v:.4f}   {desc}")
        u_c = self.combined_uncertainty()
        lines.append(f"-- Combined u_c            : {u_c:.4f}")
        lines.append(f"-- Expanded U (k=2, ~95%)   : {self.expanded_uncertainty():.4f}")
        lines.append("-- capability of the procedure (not a decision) --")
        lines.append(f"-- Critical value L_C       : {self.critical_value():.4f}   (1.645*u_c, alpha=0.05)")
        lines.append(f"-- Min. detectable displ.   : {self.minimum_detectable_displacement():.4f}   (3.29*u_c, Currie convention)")
        lines.append(f"-- Response threshold       : {self.response_threshold():.4f}   (3.645*u_c, 95% power at |BDI|>U)")
        lines.append("-- NOTE: u_0 approximated by u_c; the zero-prevalence")
        lines.append("--       null is not physically realisable.")
        return "\n".join(lines)

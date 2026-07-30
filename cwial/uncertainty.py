"""
GUM-compliant uncertainty budget engine.
Implements the Type A / Type B combination, expanded uncertainty, and the
Currie detection quantities used across the CWIMF papers (Paper 2, the
measurement architecture; Paper 3, the laboratory measurement paper).

A note on the detection quantities, and on what they can and cannot support
(Paper 3, Sections 5 and 6.3):

  * The critical value (1.645 * u_c) and the minimum detectable displacement
    (3.29 * u_0) are properties of the MEASUREMENT PROCEDURE AT THE NULL, not
    of any particular output. They characterise what the instrument can
    resolve.

  * They rest on the approximation u_0 ~ u_c, which holds only where
    displacement-independent Type B components dominate the budget. In a
    Type A dominated budget the sampling variance collapses toward the null
    and u_0 must be evaluated explicitly.

  * For a verified-false proposition the aligned prevalence is zero, so the
    null against which detection is assessed is a population in which nobody
    holds the false belief. No such population has been observed, so a
    verdict of the form "the displacement exceeds the detection floor" is
    close to true by construction and carries little information. These
    quantities are therefore reported as capability statements. Substantive
    claims rest on DIFFERENCES (between epochs or populations), where a null
    of no change is realisable.
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
        Currie critical value (1.645 * u_c at alpha = 0.05): the level a
        reading must exceed to be DISTINGUISHABLE FROM THE NULL (Currie 1968;
        ISO 11843-1). This is a capability of the procedure, not a licence to
        act: exceeding it establishes that a reading is not noise, not that
        the displacement is large enough to warrant a response. See the
        module docstring on null realisability.
        """
        return 1.645 * self.combined_uncertainty()

    # Backwards-compatible alias. 'detection_threshold' was the former name;
    # 'critical_value' matches the vocabulary of Currie 1968 / ISO 11843-1
    # and the CWIMF papers.
    def detection_threshold(self):
        return self.critical_value()

    def minimum_detectable_displacement(self):
        """
        Currie minimum detectable displacement (3.29 * u_0 with
        alpha = beta = 0.05), under the approximation u_0 ~ u_c that holds
        where displacement-independent Type B components dominate. This is
        the smallest TRUE displacement the procedure would detect with 95%
        power: a statement of instrument capability, not a threshold an
        observation "passes".
        """
        return 3.29 * self.combined_uncertainty()

    def response_threshold(self):
        """
        The displacement detectable with 95% power under the laboratory's
        two-sided response criterion |BDI| > 2*u_c (Paper 3, Section 5).
        Equals 3.645 * u_c = (2 + 1.645) * u_c. This is a larger quantity
        than the minimum detectable displacement (3.29 * u_c): at the MDD the
        response criterion retains only about 90% power, so a laboratory that
        reported its MDD as its actionable capability would overstate it. The
        two are reported together, never one in place of the other.
        """
        return 3.645 * self.combined_uncertainty()

    def summary(self):
        u_c = self.combined_uncertainty()
        U = self.expanded_uncertainty()
        crit = self.critical_value()
        mdd = self.minimum_detectable_displacement()
        resp = self.response_threshold()
        lines = [f"=== Uncertainty Budget: {self.label} ===",
                 f"Type A (u_A)              : {self.u_a:.4f}"]
        for name, (v, desc) in self.type_b.items():
            lines.append(f"Type B '{name}' (u_B)  : {v:.4f}   {desc}")
        lines.append(f"-- Combined u_c            : {u_c:.4f}")
        lines.append(f"-- Expanded U (k=2, ~95%)   : {U:.4f}")
        lines.append("-- Instrument capability (properties of the procedure at the null,")
        lines.append("   not thresholds an individual output passes; see module docstring):")
        lines.append(f"     Critical value          : {crit:.4f}   (1.645*u_c; distinguishable from null)")
        lines.append(f"     Min. detectable displ.  : {mdd:.4f}   (3.29*u_c, Currie; 95% power to detect)")
        lines.append(f"     Response capability     : {resp:.4f}   (3.645*u_c; 95% power under |BDI|>2u_c)")
        return "\n".join(lines)

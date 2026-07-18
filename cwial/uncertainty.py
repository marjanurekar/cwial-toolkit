"""
GUM-compliant uncertainty budget engine.
Implements Paper 3B, Section 5: Type A / Type B combination, expanded
uncertainty, and the Currie minimum detectable displacement (MDD).
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

    def detection_threshold(self):
        """
        Critical value: displacement above which a reading is distinguishable
        from a null result at alpha = 0.05 (Currie 1968; ISO 11843-1).
        """
        return 1.645 * self.combined_uncertainty()

    def minimum_detectable_displacement(self):
        """
        Currie MDD with alpha = beta = 0.05 (Paper 3B, eq. 8).
        Uses u_0 ~ u_c, valid where displacement-independent Type B
        components dominate the budget.
        """
        return 3.29 * self.combined_uncertainty()

    def summary(self):
        lines = [f"=== Uncertainty Budget: {self.label} ===",
                 f"Type A (u_A)              : {self.u_a:.4f}"]
        for name, (v, desc) in self.type_b.items():
            lines.append(f"Type B '{name}' (u_B)  : {v:.4f}   {desc}")
        u_c = self.combined_uncertainty()
        U = self.expanded_uncertainty()
        mdd = self.minimum_detectable_displacement()
        crit = self.detection_threshold()
        lines.append(f"-- Combined u_c            : {u_c:.4f}")
        lines.append(f"-- Expanded U (k=2, ~95%)   : {U:.4f}")
        lines.append(f"-- Detection threshold      : {crit:.4f}   (1.645*u_c, alpha=0.05)")
        lines.append(f"-- Min. detectable displ.   : {mdd:.4f}   (3.29*u_c, Currie)")
        return "\n".join(lines)

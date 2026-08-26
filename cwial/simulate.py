"""
CWIAL Monte Carlo simulation module.

Implements the two highest-priority MCM applications for CWIMF research:

  1. SYNTHETIC ATTACK SCENARIOS (Phase 1 validation, Paper 3 roadmap):
     an agent population with a KNOWN true BDI trajectory serves as a
     reference standard ANALOGOUS TO a certified reference material. The
     analogy is bounded: no CRM-issuing process under ISO 17034 stands
     behind it, and its 'certified value' is a property of the model, not
     of any real population. The full measurement pipeline
     (sampling + bias sources + uncertainty budget) is validated by
     checking that it recovers the known truth within its stated
     expanded uncertainty at the claimed coverage.

  2. DETECTION POWER CURVES (operating characteristic of the instrument):
     probability of detection P(|BDI_measured| > U) as a function of the
     true displacement, yielding the empirical 95%-power point for
     comparison with the Currie convention MDD = 3.29 * u0 (Paper 3B,
     eq. 8) and with the response threshold 3.645 * u_c actually implied
     by the |BDI| > U decision criterion.

Pure Python 3.8+ standard library. Distributions match the Paper 3B
budget exactly:
  Type A : survey sampling of n agents (naturally generated)
  d_ref  : Normal(0, 0.030)      reference classification risk
  d_instr: Normal(0, 0.050)      instrument framing bias
  d_temp : Uniform(+/-0.045)     temporal mismatch
  d_panel: Uniform(+/-0.061)     panel non-representativeness
  d_adv  : Triangular(+/-0.037)  adversarial adaptation
"""
import math
import random
import statistics
from .uncertainty import UncertaintyBudget

# Paper 3B Type B budget (name -> (kind, parameter))
DEFAULT_TYPE_B = {
    "u_B1_reference":   ("normal",     0.030),
    "u_B2_instrument":  ("normal",     0.050),
    "u_B3_temporal":    ("rectangular", 0.045),   # half-width
    "u_B4_panel":       ("rectangular", 0.061),   # half-width
    "u_B5_adversarial": ("triangular",  0.037),   # half-width
}

def _std_u(kind, param):
    """Standard uncertainty from distribution kind + parameter (GUM 4.3)."""
    if kind == "normal":       return param
    if kind == "rectangular":  return param / math.sqrt(3)
    if kind == "triangular":   return param / math.sqrt(6)
    raise ValueError(kind)

def _draw(rng, kind, param):
    """One random draw from a zero-centred distribution."""
    if kind == "normal":       return rng.gauss(0.0, param)
    if kind == "rectangular":  return rng.uniform(-param, param)
    if kind == "triangular":   return rng.triangular(-param, param, 0.0)
    raise ValueError(kind)


class AgentPopulation:
    """
    Population of N agents, each holding a binary belief on proposition F.
    Agent i accepts F with propensity theta_i; the TRUE belief prevalence
    (and hence, for a verified-false proposition, the TRUE BDI) is the
    mean of the theta_i -- known exactly, by construction.
    """
    def __init__(self, n_agents=20000, baseline_prevalence=0.10,
                 heterogeneity=20.0, seed=1):
        self.rng = random.Random(seed)
        # Beta-distributed propensities with mean = baseline_prevalence
        a = baseline_prevalence * heterogeneity
        b = (1 - baseline_prevalence) * heterogeneity
        self.theta = [self.rng.betavariate(a, b) for _ in range(n_agents)]

    @property
    def true_bdi(self):
        """Known true BDI (verified-false proposition: BDI = prevalence)."""
        return statistics.fmean(self.theta)

    def inject_campaign(self, target_shift, profile="step", steps=1):
        """
        Inject an influence campaign that raises every agent's propensity
        toward acceptance of F by a known amount.
          profile='step': full shift applied at once (AI mass-content case)
          profile='ramp': shift applied in `steps` equal increments; returns
                          the list of true BDI values after each increment.
        The shift is applied multiplicatively toward 1 so propensities stay
        in [0,1]: theta <- theta + shift_fraction * (1 - theta), where
        shift_fraction is solved so that the population mean moves by
        exactly `target_shift`.
        """
        trajectory = []
        per_step = target_shift / steps
        for _ in range(steps):
            mean_now = statistics.fmean(self.theta)
            headroom = 1.0 - mean_now
            if headroom <= 0:
                break
            f = min(1.0, per_step / headroom)
            self.theta = [t + f * (1.0 - t) for t in self.theta]
            trajectory.append(self.true_bdi)
        return trajectory if profile == "ramp" else self.true_bdi

    def survey(self, n_sample, rng=None):
        """
        Draw a survey: sample n agents without replacement, each responds
        'accept' with probability theta_i. Returns observed prevalence.
        This generates the Type A sampling error naturally.
        """
        rng = rng or self.rng
        idx = rng.sample(range(len(self.theta)), n_sample)
        hits = sum(1 for i in idx if rng.random() < self.theta[i])
        return hits / n_sample


def measure_once(pop, n_sample, rng, type_b=DEFAULT_TYPE_B, k=2):
    """
    One complete simulated CWIAL measurement:
      observed prevalence  = survey draw          (Type A, natural)
      + bias draws         = one realisation of each Type B source
      -> reported BDI, with the standard budget's U(BDI).
    Returns (bdi_reported, U, u_c).
    """
    p_obs = pop.survey(n_sample, rng)
    bias = sum(_draw(rng, kind, prm) for kind, prm in type_b.values())
    bdi_reported = p_obs + bias

    # The laboratory's declared budget (it does NOT know the bias draws)
    p_hat = min(max(bdi_reported, 1e-6), 1 - 1e-6)
    u_a = math.sqrt(p_hat * (1 - p_hat) / n_sample)
    u_c = math.sqrt(u_a**2 + sum(_std_u(kind, prm)**2
                                  for kind, prm in type_b.values()))
    return bdi_reported, k * u_c, u_c


def validate_recovery(true_bdi_target=0.42, n_agents=20000, n_sample=1467,
                       trials=500, seed=42, verbose=True):
    """
    APPLICATION 1 -- known-truth recovery validation.
    Builds a population displaced to a known true BDI, runs `trials`
    complete measurements, and reports the fraction of trials whose
    interval [BDI - U, BDI + U] covers the known truth.
    PASS criterion: coverage >= 0.93 for k = 2 (nominal 0.95, MC noise
    at 500 trials is about +/-0.02).
    """
    rng = random.Random(seed)
    pop = AgentPopulation(n_agents, baseline_prevalence=0.10, seed=seed)
    pop.inject_campaign(true_bdi_target - pop.true_bdi, profile="step")
    truth = pop.true_bdi

    covered, errors = 0, []
    for _ in range(trials):
        bdi, U, _ = measure_once(pop, n_sample, rng)
        errors.append(bdi - truth)
        if abs(bdi - truth) <= U:
            covered += 1
    coverage = covered / trials
    if verbose:
        print(f"[Recovery] true BDI = {truth:.4f} (known by construction)")
        print(f"[Recovery] mean measured BDI = {truth + statistics.fmean(errors):.4f}")
        print(f"[Recovery] empirical sd of error = {statistics.pstdev(errors):.4f} "
              f"(budget u_c ~ 0.076)")
        print(f"[Recovery] coverage at k=2: {coverage:.3f} over {trials} trials "
              f"-> {'PASS' if coverage >= 0.93 else 'FAIL'}")
    return coverage, statistics.pstdev(errors)


def power_curve(true_bdi_values=(0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.42),
                n_agents=20000, n_sample=1467, trials=400, seed=7, verbose=True):
    """
    APPLICATION 2 -- detection power curve (operating characteristic).
    For each true displacement, the detection rule is |BDI| > U (the
    Paper 3B response criterion). Returns list of (true_bdi, power).
    Also reports the empirical 95%-power point, which should land near
    the response threshold 3.645*u_c ~ 0.28 rather than the Currie MDD
    3.29*u0 ~ 0.25 -- the latter is paired with the weaker critical value
    1.645*u0, not with the |BDI| > U criterion used here.
    """
    results = []
    for tb in true_bdi_values:
        rng = random.Random(seed + int(tb * 1000))
        pop = AgentPopulation(n_agents, baseline_prevalence=max(tb, 1e-3),
                               seed=seed + int(tb * 1000))
        # nudge population mean to exactly tb
        delta = tb - pop.true_bdi
        if abs(delta) > 1e-6 and tb > 0:
            pop.inject_campaign(delta, profile="step")
        detects = 0
        for _ in range(trials):
            bdi, U, _ = measure_once(pop, n_sample, rng)
            if abs(bdi) > U:
                detects += 1
        power = detects / trials
        results.append((tb, power))
        if verbose:
            bar = "#" * int(power * 40)
            print(f"[Power] true BDI = {tb:.2f}  P(detect) = {power:.3f}  {bar}")
    mdd_emp = next((tb for tb, pw in results if pw >= 0.95 and tb > 0), None)
    if verbose:
        print(f"[Power] empirical 95%-power point: "
              f"{mdd_emp if mdd_emp is not None else '> max simulated'}"
              f"   (response threshold 3.645 x u_c ~ 0.28; "
              f"Currie MDD 3.29 x u0 ~ 0.25)")
    return results, mdd_emp

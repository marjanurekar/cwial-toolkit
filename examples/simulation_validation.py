"""
Runs both Monte Carlo applications of the CWIAL simulation module and
verifies the results against the Paper 3B published values.

Usage:  python examples/simulation_validation.py     (runtime ~1-2 min)

Expected verification outcomes:
  1. Known-truth recovery coverage at k=2 in [0.93, 1.00]  (nominal 0.95)
  2. Empirical error sd within ~15% of the budget u_c = 0.076
  3. False-detection rate at true BDI = 0 below ~0.05
  4. Empirical MDD consistent with the Currie approximation ~0.25
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cwial.simulate import validate_recovery, power_curve

def main():
    t0 = time.time()
    print("=" * 64)
    print("APPLICATION 1 -- Synthetic attack scenario, known-truth recovery")
    print("=" * 64)
    coverage, err_sd = validate_recovery(true_bdi_target=0.42,
                                          trials=500, seed=42)
    print()
    print("=" * 64)
    print("APPLICATION 2 -- Detection power curve (operating characteristic)")
    print("=" * 64)
    results, mdd_emp = power_curve(trials=400, seed=7)
    print()
    print("=" * 64)
    print("VERIFICATION SUMMARY")
    print("=" * 64)
    p0 = results[0][1]  # false-detection rate at true BDI = 0
    checks = [
        ("Coverage in [0.93, 1.00]",            0.93 <= coverage <= 1.00),
        ("Error sd within 15% of u_c=0.076",    abs(err_sd - 0.076) / 0.076 <= 0.15),
        ("False-detection rate at BDI=0 < 0.05", p0 < 0.05),
        ("Empirical MDD within [0.20, 0.30]",   mdd_emp is not None and 0.20 <= mdd_emp <= 0.30),
    ]
    ok = True
    for label, passed in checks:
        print(f"  {'PASS' if passed else 'FAIL':4} | {label}")
        ok = ok and passed
    print(f"\n{'ALL VERIFICATIONS PASSED' if ok else 'SOME CHECKS FAILED'}"
          f"   (runtime {time.time()-t0:.0f}s)")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())

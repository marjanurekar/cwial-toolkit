"""
Characterise an NCS scoring instrument (e.g. an LLM) as a measurement device.
Runs the full metrological validation on synthetic data with known injected
parameters and verifies the analysis recovers them.

Usage:  python examples/ncs_instrument_validation.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cwial.ncs_validation import run_validation

if __name__ == "__main__":
    run_validation(seed=1)

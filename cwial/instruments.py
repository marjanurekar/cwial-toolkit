"""
Instrument registry -- ISO/IEC 17025 clause 6.4 equivalent, minimal version.
CSV-backed for zero-dependency simplicity; can be swapped for SQLite later
without changing the public interface.
"""
import csv
import datetime
from pathlib import Path

FIELDS = ["name", "version", "type", "calibration_date",
          "next_calibration_due", "known_bias", "notes"]


class InstrumentRegistry:
    def __init__(self, path="data/instruments.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    def register(self, name, version, itype, calibration_date=None,
                 next_calibration_days=180, known_bias="none documented", notes=""):
        calibration_date = calibration_date or datetime.date.today().isoformat()
        next_due = (datetime.date.fromisoformat(calibration_date) +
                    datetime.timedelta(days=next_calibration_days)).isoformat()
        with open(self.path, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow({
                "name": name, "version": version, "type": itype,
                "calibration_date": calibration_date,
                "next_calibration_due": next_due,
                "known_bias": known_bias, "notes": notes
            })
        print(f"[Instruments] Registered '{name}' v{version} ({itype}); "
              f"next calibration due {next_due}")

    def due_for_calibration(self):
        today = datetime.date.today().isoformat()
        overdue = []
        with open(self.path) as f:
            for row in csv.DictReader(f):
                if row["next_calibration_due"] < today:
                    overdue.append(row)
        if overdue:
            print(f"[Instruments] WARNING: {len(overdue)} instrument(s) overdue for calibration:")
            for row in overdue:
                print(f"   - {row['name']} v{row['version']} "
                      f"(due {row['next_calibration_due']})")
        return overdue

    def list_all(self):
        with open(self.path) as f:
            return list(csv.DictReader(f))

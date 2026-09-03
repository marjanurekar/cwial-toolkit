"""
Instrument registry - ISO/IEC 17025 clause 6.4 equivalent, minimal version.
CSV-backed for zero-dependency simplicity; can be swapped for SQLite later
without changing the public interface.

Two rules the registry enforces (0.3.0):

  * An instrument is unique on (name, version). Re-running a seeding script
    does not create duplicate rows.
  * A survey instrument must be registered with an explicit calibration_date,
    which for a survey is the fieldwork date. Defaulting to today would write
    a false fact about the instrument: a wave fielded in 2010 was not
    calibrated in whatever year the script happens to run.

A completed survey wave cannot be re-fielded, so it has no next calibration
due. Those rows carry a non-date marker instead.
"""
import csv
import datetime
from pathlib import Path

FIELDS = ["name", "version", "type", "calibration_date",
          "next_calibration_due", "known_bias", "notes"]

NOT_RECALIBRABLE = "not applicable (completed wave)"


class InstrumentRegistry:
    def __init__(self, path="data/instruments.csv", verbose=True):
        self.path = Path(path)
        self.verbose = verbose
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def _exists(self, name, version):
        return any(r["name"] == name and r["version"] == version
                   for r in self.list_all())

    def register(self, name, version, itype, calibration_date=None,
                 next_calibration_days=180, known_bias="none documented",
                 notes=""):
        """
        Register an instrument. Returns True if a row was written, False if
        this (name, version) was already on file.

        calibration_date is required when itype is 'survey': give the
        fieldwork date in ISO 8601 form.
        """
        if itype == "survey":
            if calibration_date is None:
                raise ValueError(
                    "calibration_date is required for a survey instrument. "
                    "Give the fieldwork date; defaulting to today would record "
                    "a false fact about the instrument.")
            next_calibration_days = None

        calibration_date = calibration_date or datetime.date.today().isoformat()
        if next_calibration_days is None:
            next_due = NOT_RECALIBRABLE
        else:
            next_due = (datetime.date.fromisoformat(calibration_date) +
                        datetime.timedelta(days=next_calibration_days)).isoformat()

        if self._exists(name, version):
            self._log(f"[Instruments] '{name}' v{version} already on file, "
                      f"not duplicated.")
            return False

        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow({
                "name": name, "version": version, "type": itype,
                "calibration_date": calibration_date,
                "next_calibration_due": next_due,
                "known_bias": known_bias, "notes": notes
            })
        self._log(f"[Instruments] Registered '{name}' v{version} ({itype}); "
                  f"calibrated {calibration_date}; next due {next_due}")
        return True

    def due_for_calibration(self):
        """Rows whose next calibration date has passed. Non-date markers skipped."""
        today = datetime.date.today().isoformat()
        overdue = []
        for row in self.list_all():
            due = row["next_calibration_due"]
            try:
                datetime.date.fromisoformat(due)
            except ValueError:
                continue
            if due < today:
                overdue.append(row)
        if overdue:
            self._log(f"[Instruments] WARNING: {len(overdue)} instrument(s) "
                      f"overdue for calibration:")
            for row in overdue:
                self._log(f"   - {row['name']} v{row['version']} "
                          f"(due {row['next_calibration_due']})")
        return overdue

    def list_all(self):
        with open(self.path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

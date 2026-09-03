"""
Verified Factual Reference Base (VFRB) - SQLite-backed reference standard.
Implements the schema from Paper 3, Section 7.1.

Register integrity (0.3.0). Two properties are enforced by the store itself
rather than left to the caller:

  * A source is unique per proposition. Re-running a seeding script cannot
    inflate the source count, so the three-source check reports evidential
    sufficiency and not how often a script was executed.
  * entry_date is written once. A later call updates last_verified and leaves
    the original entry date intact, because the register is an audit trail
    and an audit trail whose creation dates move is not one.

Databases created before 0.3.0 lack the uniqueness constraint. The
constructor detects this and warns; rebuild from a fresh file.
"""
import sqlite3
import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS propositions (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    truth_value TEXT NOT NULL CHECK(truth_value IN ('TRUE','FALSE','CONTESTED')),
    numeric_value REAL,
    numeric_uncertainty REAL,
    tier INTEGER NOT NULL CHECK(tier IN (1,2,3)),
    entry_date TEXT NOT NULL,
    last_verified TEXT NOT NULL,
    expiry_date TEXT,
    maintainer TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposition_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    url TEXT,
    isrg_grade TEXT CHECK(isrg_grade IN ('I','II','III','IV','V')),
    accessed_date TEXT NOT NULL,
    UNIQUE(proposition_id, source_name),
    FOREIGN KEY(proposition_id) REFERENCES propositions(id)
);
"""

TIER_UNCERTAINTY_GUIDANCE = {
    1: "u_VFRB < 2%  (scientific consensus)",
    2: "u_VFRB 2-10% (official record)",
    3: "u_VFRB 10-30% (contested documentation)",
}

MIN_INDEPENDENT_SOURCES = 3


class VFRB:
    def __init__(self, db_path="data/vfrb.db", verbose=True):
        self.db_path = Path(db_path)
        self.verbose = verbose
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._check_uniqueness_constraint()

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def _check_uniqueness_constraint(self):
        """Warn if this database predates the 0.3.0 uniqueness constraint."""
        cur = self.conn.execute("PRAGMA index_list('sources')")
        for row in cur.fetchall():
            if row[2]:  # unique flag
                cols = [r[2] for r in
                        self.conn.execute(f"PRAGMA index_info('{row[1]}')").fetchall()]
                if set(cols) == {"proposition_id", "source_name"}:
                    return
        self._log(
            "[VFRB] WARNING: this database was created before v0.3.0 and has no "
            "uniqueness constraint on (proposition_id, source_name). Duplicate "
            "sources can inflate the source count. Rebuild from a fresh file.")

    def add_proposition(self, prop_id, text, truth_value, tier, maintainer,
                        numeric_value=None, numeric_uncertainty=None,
                        expiry_days=365, notes=""):
        """
        Insert or update a proposition. entry_date is set on first write only.
        A later call updates last_verified and expiry_date and preserves the
        original entry_date.
        """
        today = datetime.date.today().isoformat()
        expiry = (datetime.date.today() +
                  datetime.timedelta(days=expiry_days)).isoformat()
        row = self.conn.execute(
            "SELECT entry_date FROM propositions WHERE id = ?", (prop_id,)
        ).fetchone()
        entry_date = row[0] if row else today
        self.conn.execute(
            """INSERT OR REPLACE INTO propositions
               (id, text, truth_value, numeric_value, numeric_uncertainty,
                tier, entry_date, last_verified, expiry_date, maintainer, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (prop_id, text, truth_value, numeric_value, numeric_uncertainty,
             tier, entry_date, today, expiry, maintainer, notes)
        )
        self.conn.commit()
        action = "Updated" if row else "Added"
        self._log(f"[VFRB] {action} proposition '{prop_id}' (Tier {tier}, "
                  f"{TIER_UNCERTAINTY_GUIDANCE[tier]}; entry_date {entry_date})")

    def add_source(self, prop_id, source_name, isrg_grade, url="",
                   accessed_date=None):
        """
        Register a source for the TRUTH VALUE of a proposition. Returns True if
        a new row was written, False if this source was already on file.

        The survey or classifier used to measure belief is the measuring
        instrument, not a source for the reference value. Register it in the
        instrument registry instead.
        """
        accessed_date = accessed_date or datetime.date.today().isoformat()
        cur = self.conn.execute(
            """INSERT OR IGNORE INTO sources
               (proposition_id, source_name, url, isrg_grade, accessed_date)
               VALUES (?,?,?,?,?)""",
            (prop_id, source_name, url, isrg_grade, accessed_date)
        )
        self.conn.commit()
        if cur.rowcount == 0:
            self._log(f"[VFRB] Source already on file for '{prop_id}', not "
                      f"duplicated: {source_name[:60]}")
            return False
        return True

    def get_proposition(self, prop_id):
        cur = self.conn.execute("SELECT * FROM propositions WHERE id = ?", (prop_id,))
        row = cur.fetchone()
        if not row:
            raise KeyError(f"No VFRB entry for proposition_id='{prop_id}'")
        cols = [d[0] for d in cur.description]
        entry = dict(zip(cols, row))
        entry["sources"] = self.get_sources(prop_id)
        return entry

    def get_sources(self, prop_id):
        cur = self.conn.execute(
            "SELECT source_name, url, isrg_grade, accessed_date FROM sources "
            "WHERE proposition_id = ?", (prop_id,)
        )
        return [dict(zip(["source_name", "url", "isrg_grade", "accessed_date"], r))
                for r in cur.fetchall()]

    def check_expiry(self):
        """Return propositions past their expiry_date, due for re-verification."""
        today = datetime.date.today().isoformat()
        expired = self.conn.execute(
            "SELECT id, text, expiry_date FROM propositions WHERE expiry_date < ?",
            (today,)
        ).fetchall()
        if expired:
            self._log(f"[VFRB] WARNING: {len(expired)} proposition(s) overdue "
                      f"for re-verification:")
            for pid, text, exp in expired:
                self._log(f"   - {pid} (expired {exp}): {text[:60]}...")
        return expired

    def list_propositions(self):
        return self.conn.execute(
            "SELECT id, text, truth_value, tier FROM propositions").fetchall()

    def source_count(self, prop_id):
        """
        Minimum-source check. Counts sources for the truth value only; the
        measuring instrument is not among them.
        """
        n = len(self.get_sources(prop_id))
        if n < MIN_INDEPENDENT_SOURCES:
            self._log(f"[VFRB] WARNING: '{prop_id}' has only {n} source(s); "
                      f"minimum {MIN_INDEPENDENT_SOURCES} independent sources "
                      f"recommended before operational use. Declare the "
                      f"shortfall in the entry notes; do not count the "
                      f"measuring instrument to reach the minimum.")
        return n

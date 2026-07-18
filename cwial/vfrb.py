"""
Verified Factual Reference Base (VFRB) — SQLite-backed reference standard.
Implements the schema from Paper 3, Section 7.1.
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
    FOREIGN KEY(proposition_id) REFERENCES propositions(id)
);
"""

TIER_UNCERTAINTY_GUIDANCE = {
    1: "u_VFRB < 2%  (scientific consensus)",
    2: "u_VFRB 2-10% (official record)",
    3: "u_VFRB 10-30% (contested documentation)",
}


class VFRB:
    def __init__(self, db_path="data/vfrb.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def add_proposition(self, prop_id, text, truth_value, tier, maintainer,
                         numeric_value=None, numeric_uncertainty=None,
                         expiry_days=365, notes=""):
        today = datetime.date.today().isoformat()
        expiry = (datetime.date.today() + datetime.timedelta(days=expiry_days)).isoformat()
        self.conn.execute(
            """INSERT OR REPLACE INTO propositions
               (id, text, truth_value, numeric_value, numeric_uncertainty,
                tier, entry_date, last_verified, expiry_date, maintainer, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (prop_id, text, truth_value, numeric_value, numeric_uncertainty,
             tier, today, today, expiry, maintainer, notes)
        )
        self.conn.commit()
        print(f"[VFRB] Added proposition '{prop_id}' (Tier {tier}, "
              f"{TIER_UNCERTAINTY_GUIDANCE[tier]})")

    def add_source(self, prop_id, source_name, isrg_grade, url="", accessed_date=None):
        accessed_date = accessed_date or datetime.date.today().isoformat()
        self.conn.execute(
            """INSERT INTO sources (proposition_id, source_name, url, isrg_grade, accessed_date)
               VALUES (?,?,?,?,?)""",
            (prop_id, source_name, url, isrg_grade, accessed_date)
        )
        self.conn.commit()

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
            "SELECT source_name, url, isrg_grade, accessed_date FROM sources WHERE proposition_id = ?",
            (prop_id,)
        )
        return [dict(zip(["source_name", "url", "isrg_grade", "accessed_date"], r))
                for r in cur.fetchall()]

    def check_expiry(self):
        """Return list of propositions past their expiry_date -- due for re-verification."""
        today = datetime.date.today().isoformat()
        cur = self.conn.execute(
            "SELECT id, text, expiry_date FROM propositions WHERE expiry_date < ?", (today,)
        )
        expired = cur.fetchall()
        if expired:
            print(f"[VFRB] WARNING: {len(expired)} proposition(s) overdue for re-verification:")
            for pid, text, exp in expired:
                print(f"   - {pid} (expired {exp}): {text[:60]}...")
        return expired

    def list_propositions(self):
        cur = self.conn.execute("SELECT id, text, truth_value, tier FROM propositions")
        return cur.fetchall()

    def source_count(self, prop_id):
        """ISO/IEC 17025-style minimum-source check (Paper 3 recommends >=3 independent sources)."""
        n = len(self.get_sources(prop_id))
        if n < 3:
            print(f"[VFRB] WARNING: '{prop_id}' has only {n} source(s); "
                  f"minimum 3 independent sources recommended before operational use.")
        return n

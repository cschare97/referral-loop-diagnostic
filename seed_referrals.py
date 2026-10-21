"""
seed_referrals.py - build a synthetic referral dataset with KNOWN failures.

Everything here is invented. Names, dates and specialties are random.
The point: every broken referral is labeled in the `ground_truth` table,
so a diagnostic can later be scored on how many it catches and names correctly.

Usage:
    python seed_referrals.py                # writes referral_seed.db
    python seed_referrals.py --db other.db --asof 2026-10-20 --seed 7
"""
import argparse
import random
import sqlite3
from datetime import date, timedelta

FIRST = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie",
         "Avery", "Quinn", "Drew", "Reese", "Skyler", "Parker", "Rowan", "Emery"]
LAST = ["Alder", "Birch", "Cedar", "Dunn", "Ellis", "Finch", "Grove", "Hale",
        "Ives", "Jarvis", "Kemp", "Lowe", "Marsh", "Nash", "Oakes", "Pryor"]
SPECIALTIES = ["Cardiology", "Dermatology", "Orthopedics", "Gastroenterology",
               "Neurology", "Ophthalmology", "Radiology-MRI", "Radiology-CT"]

# Failure types the diagnostic should learn to name.
# Each: (label, how many to seed)
FAILURES = [
    ("auth_not_started",      5),  # needs prior auth, none requested
    ("auth_denied",           5),  # auth requested and denied, nobody acted
    ("never_scheduled",       5),  # authorized (or not needed), patient never scheduled
    ("missing_data",          5),  # referral lacks info needed for follow-up
    ("completed_not_in_chart", 5), # visit happened, no record came back
    ("result_not_reviewed",   5),  # result received, provider never reviewed
]
HEALTHY_IN_PROGRESS = 5   # normal, young referrals still moving
HEALTHY_CLOSED = 5        # full loop closed

SCHEMA = """
DROP TABLE IF EXISTS ground_truth;
DROP TABLE IF EXISTS referrals;
DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    dob TEXT NOT NULL
);

-- One row per referral, one date column per lifecycle step.
-- NULL date = that step has not happened.
CREATE TABLE referrals (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    specialty TEXT NOT NULL,
    created_date TEXT NOT NULL,
    auth_required INTEGER NOT NULL,      -- 0/1
    auth_requested_date TEXT,
    auth_status TEXT,                    -- NULL, 'approved', 'denied'
    auth_decision_date TEXT,
    scheduled_date TEXT,
    completed_date TEXT,
    result_received_date TEXT,
    reviewed_date TEXT,
    reason_for_referral TEXT,            -- NULL/empty = missing data
    diagnosis_code TEXT                  -- NULL = missing data
);

-- Answer key. A diagnostic must NOT read this table; it is for scoring only.
CREATE TABLE ground_truth (
    referral_id INTEGER PRIMARY KEY REFERENCES referrals(id),
    seeded_state TEXT NOT NULL           -- failure label, 'healthy_in_progress', or 'healthy_closed'
);
"""


def iso(d):
    return d.isoformat() if d else None


def build(db_path, asof, seed):
    rng = random.Random(seed)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)

    next_patient = 1
    next_ref = 1

    def new_patient():
        nonlocal next_patient
        pid = next_patient
        next_patient += 1
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        dob = date(rng.randint(1945, 2005), rng.randint(1, 12), rng.randint(1, 28))
        con.execute("INSERT INTO patients VALUES (?,?,?)", (pid, name, iso(dob)))
        return pid

    def add(state, **f):
        """Insert one referral + its answer-key row."""
        nonlocal next_ref
        rid = next_ref
        next_ref += 1
        row = dict(
            auth_required=0, auth_requested_date=None, auth_status=None,
            auth_decision_date=None, scheduled_date=None, completed_date=None,
            result_received_date=None, reviewed_date=None,
            reason_for_referral="Evaluate and treat", diagnosis_code="R99",
        )
        row.update(f)
        row.update(id=rid, patient_id=new_patient(), specialty=rng.choice(SPECIALTIES))
        cols = ", ".join(row.keys())
        marks = ", ".join("?" for _ in row)
        con.execute(f"INSERT INTO referrals ({cols}) VALUES ({marks})", list(row.values()))
        con.execute("INSERT INTO ground_truth VALUES (?,?)", (rid, state))

    def ago(lo, hi):
        return asof - timedelta(days=rng.randint(lo, hi))

    # ---- seeded failures ------------------------------------------------
    for _ in range(5):  # auth needed, never requested
        c = ago(25, 90)
        add("auth_not_started", created_date=iso(c), auth_required=1)

    for _ in range(5):  # auth denied, then nothing
        c = ago(40, 120)
        req = c + timedelta(days=rng.randint(1, 4))
        dec = req + timedelta(days=rng.randint(5, 14))
        add("auth_denied", created_date=iso(c), auth_required=1,
            auth_requested_date=iso(req), auth_status="denied",
            auth_decision_date=iso(dec))

    for _ in range(5):  # cleared to schedule, never scheduled
        c = ago(35, 110)
        if rng.random() < 0.5:   # no auth needed
            add("never_scheduled", created_date=iso(c), auth_required=0)
        else:                    # auth approved
            req = c + timedelta(days=2)
            dec = req + timedelta(days=rng.randint(3, 10))
            add("never_scheduled", created_date=iso(c), auth_required=1,
                auth_requested_date=iso(req), auth_status="approved",
                auth_decision_date=iso(dec))

    for _ in range(5):  # missing clinical info
        c = ago(20, 80)
        gap = rng.choice(["reason", "dx", "both"])
        add("missing_data", created_date=iso(c),
            reason_for_referral=None if gap in ("reason", "both") else "Evaluate and treat",
            diagnosis_code=None if gap in ("dx", "both") else "R99")

    for _ in range(5):  # visit done, nothing came back
        c = ago(60, 150)
        sched = c + timedelta(days=rng.randint(10, 25))
        done = sched + timedelta(days=rng.randint(0, 3))
        add("completed_not_in_chart", created_date=iso(c),
            scheduled_date=iso(sched), completed_date=iso(done))

    for _ in range(5):  # result in, never reviewed
        c = ago(60, 150)
        sched = c + timedelta(days=rng.randint(10, 25))
        done = sched + timedelta(days=rng.randint(0, 3))
        got = done + timedelta(days=rng.randint(3, 14))
        add("result_not_reviewed", created_date=iso(c),
            scheduled_date=iso(sched), completed_date=iso(done),
            result_received_date=iso(got))

    # ---- healthy controls (must NOT be flagged) ------------------------
    for _ in range(HEALTHY_IN_PROGRESS):  # young, still moving normally
        c = ago(1, 8)
        add("healthy_in_progress", created_date=iso(c))

    for _ in range(HEALTHY_CLOSED):       # full loop closed
        c = ago(60, 150)
        sched = c + timedelta(days=rng.randint(7, 20))
        done = sched + timedelta(days=rng.randint(0, 3))
        got = done + timedelta(days=rng.randint(2, 7))
        rev = got + timedelta(days=rng.randint(1, 4))
        add("healthy_closed", created_date=iso(c), scheduled_date=iso(sched),
            completed_date=iso(done), result_received_date=iso(got),
            reviewed_date=iso(rev))

    con.commit()
    total = con.execute("SELECT COUNT(*) FROM referrals").fetchone()[0]
    counts = con.execute(
        "SELECT seeded_state, COUNT(*) FROM ground_truth GROUP BY 1 ORDER BY 1"
    ).fetchall()
    con.close()
    return total, counts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="referral_seed.db")
    ap.add_argument("--asof", default=date.today().isoformat(),
                    help="reference 'today' (YYYY-MM-DD)")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    total, counts = build(a.db, date.fromisoformat(a.asof), a.seed)
    print(f"Wrote {total} referrals to {a.db} (as of {a.asof}, seed {a.seed})")
    for state, n in counts:
        print(f"  {state:24s} {n}")

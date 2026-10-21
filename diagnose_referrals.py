"""
diagnose_referrals.py - find where each referral's loop broke, and who owns the fix.

Reads ONLY the `referrals` and `patients` tables. It never touches `ground_truth`
during diagnosis; the answer key is opened afterward, in --score mode, purely to grade.

Usage:
    python diagnose_referrals.py --asof 2026-10-20            # print report
    python diagnose_referrals.py --asof 2026-10-20 --score    # also grade vs answer key
    python diagnose_referrals.py --asof 2026-10-20 --csv out.csv
"""
import argparse
import csv
import sqlite3
from datetime import date

# Days a step may sit before it counts as stuck. Tune these; they are judgment calls,
# not published standards.
GRACE = {
    "auth_not_started": 7,    # auth needed, nobody requested it
    "auth_pending": 14,       # requested, no decision
    "never_scheduled": 14,    # cleared to schedule, still unscheduled
    "scheduled_not_done": 7,  # appointment date passed, no completion
    "completed_not_in_chart": 14,
    "result_not_reviewed": 7,
}

# cause -> (who acts, what to do)
OWNERS = {
    "missing_data": ("Ordering staff", "Add reason for referral / diagnosis code"),
    "auth_not_started": ("Referral coordinator", "Submit prior authorization request"),
    "auth_pending": ("Referral coordinator", "Follow up with payer on pending auth"),
    "auth_denied": ("Referral coordinator + provider", "Appeal, or choose alternate path with provider"),
    "never_scheduled": ("Front desk / patient outreach", "Contact patient to schedule"),
    "scheduled_not_done": ("Referral coordinator", "Confirm whether visit happened or was missed"),
    "completed_not_in_chart": ("Referral coordinator", "Request visit note / result from specialist"),
    "result_not_reviewed": ("Ordering provider", "Review result and document next step"),
    "in_progress": ("-", "No action yet; within normal time"),
    "closed": ("-", "Loop closed"),
}


def d(s):
    return date.fromisoformat(s) if s else None


def days(a, b):
    return (a - b).days


def diagnose(r, asof):
    """Return (cause, days_stuck) for one referral row (dict).

    Walks the lifecycle and stops at the first step that is missing AND overdue.
    days_stuck = days since the last step that did happen.
    """
    created = d(r["created_date"])

    if r["reviewed_date"]:
        return "closed", 0

    # Missing clinical info blocks everything downstream, so flag it first.
    if not (r["reason_for_referral"] or "").strip() or not (r["diagnosis_code"] or "").strip():
        return "missing_data", days(asof, created)

    if r["result_received_date"]:
        age = days(asof, d(r["result_received_date"]))
        return ("result_not_reviewed", age) if age > GRACE["result_not_reviewed"] else ("in_progress", age)

    if r["completed_date"]:
        age = days(asof, d(r["completed_date"]))
        return ("completed_not_in_chart", age) if age > GRACE["completed_not_in_chart"] else ("in_progress", age)

    if r["scheduled_date"]:
        sched = d(r["scheduled_date"])
        if sched < asof:
            age = days(asof, sched)
            return ("scheduled_not_done", age) if age > GRACE["scheduled_not_done"] else ("in_progress", age)
        return "in_progress", days(asof, created)  # appointment still upcoming

    # Not scheduled yet. Auth path first.
    if r["auth_required"]:
        if not r["auth_requested_date"]:
            age = days(asof, created)
            return ("auth_not_started", age) if age > GRACE["auth_not_started"] else ("in_progress", age)
        if not r["auth_status"]:
            age = days(asof, d(r["auth_requested_date"]))
            return ("auth_pending", age) if age > GRACE["auth_pending"] else ("in_progress", age)
        if r["auth_status"] == "denied":
            return "auth_denied", days(asof, d(r["auth_decision_date"]))
        # approved -> fall through to scheduling check, clock starts at decision
        age = days(asof, d(r["auth_decision_date"]))
    else:
        age = days(asof, created)

    return ("never_scheduled", age) if age > GRACE["never_scheduled"] else ("in_progress", age)


def load(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """SELECT r.*, p.name AS patient_name
           FROM referrals r JOIN patients p ON p.id = r.patient_id"""
    ).fetchall()
    return con, [dict(x) for x in rows]


def score(con, results):
    """Compare diagnosis to the answer key. Healthy states collapse to one bucket."""
    truth = dict(con.execute("SELECT referral_id, seeded_state FROM ground_truth"))
    norm = lambda s: "healthy" if s in ("healthy_in_progress", "healthy_closed", "in_progress", "closed") else s
    right, wrong = 0, []
    for res in results:
        t, g = norm(truth[res["id"]]), norm(res["cause"])
        if t == g:
            right += 1
        else:
            wrong.append((res["id"], truth[res["id"]], res["cause"]))
    return right, len(results), wrong


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="referral_seed.db")
    ap.add_argument("--asof", default=date.today().isoformat())
    ap.add_argument("--score", action="store_true", help="grade against ground_truth")
    ap.add_argument("--csv", help="also write the report to this CSV path")
    a = ap.parse_args()
    asof = date.fromisoformat(a.asof)

    con, rows = load(a.db)
    results = []
    for r in rows:
        cause, stuck = diagnose(r, asof)
        owner, action = OWNERS[cause]
        results.append(dict(id=r["id"], patient=r["patient_name"], specialty=r["specialty"],
                            cause=cause, days_stuck=stuck, owner=owner, action=action))

    flagged = [x for x in results if x["cause"] not in ("in_progress", "closed")]
    flagged.sort(key=lambda x: -x["days_stuck"])

    print(f"As of {asof}: {len(results)} referrals, {len(flagged)} need action\n")
    print(f"{'ID':>3}  {'Days':>4}  {'Cause':<24} {'Owner':<30} Action")
    for x in flagged:
        print(f"{x['id']:>3}  {x['days_stuck']:>4}  {x['cause']:<24} {x['owner']:<30} {x['action']}")

    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(flagged)
        print(f"\nWrote {len(flagged)} rows to {a.csv}")

    if a.score:
        right, total, wrong = score(con, results)
        print(f"\nScore: {right}/{total} correct")
        for rid, truth, got in wrong:
            print(f"  MISS id {rid}: truth={truth}, diagnosed={got}")
    con.close()

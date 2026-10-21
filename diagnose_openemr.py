"""
diagnose_openemr.py - find stalled referrals in a live OpenEMR database.

Reads OpenEMR's native referral data (transactions + lbt_data, title 'LBTref').
No extra libraries: it shells out to `docker exec ... mariadb`.

What OpenEMR tracks natively is limited (no auth, scheduling, or review fields),
so this finds four states:
    missing_data  - reason or diagnosis is blank
    no_reply      - referral is old and has no reply date
    date_problem  - unreadable date, future referral, or reply dated before referral
    reply_empty   - reply date on file but findings are blank
    in_progress   - recent, still within normal time
    closed        - reply on file with findings
Other problems on the same referral are listed under "Also".

Usage:
    python3 diagnose_openemr.py --asof 2026-10-20
    python3 diagnose_openemr.py --asof 2026-10-20 --score   # grade seeded DIAG-TEST rows
"""
import argparse
import subprocess
from datetime import date

CONTAINER = "development-easy-mysql-1"
DB_USER, DB_PASS, DB_NAME = "root", "root", "openemr"

NO_REPLY_GRACE_DAYS = 30   # judgment call, not a published standard

OWNERS = {
    "missing_data": ("Ordering staff", "Add reason for referral / diagnosis"),
    "no_reply": ("Referral coordinator", "Contact specialist for visit note / result"),
    "date_problem": ("Ordering staff", "Correct the referral/reply date"),
    "reply_empty": ("Referral coordinator", "Reply logged with no findings; get the actual note"),
    "in_progress": ("-", "No action yet; within normal time"),
    "closed": ("-", "Reply on file with findings"),
}

# One row per referral; lbt_data pivoted into columns.
QUERY = """
SELECT x.id, x.pid, x.patient, x.groupname, x.refer_date,
  CASE WHEN x.refer_to REGEXP '^[0-9]+$'
       THEN COALESCE(NULLIF(u.specialty,''), CONCAT('Dr. ', u.lname))
       ELSE x.refer_to END AS refer_to,
  x.body, x.refer_diag, x.reply_date, x.reply_findings
FROM (
  SELECT t.id, t.pid, CONCAT(p.fname,' ',p.lname) AS patient, t.groupname,
    MAX(CASE WHEN l.field_id='refer_date'  THEN l.field_value END) AS refer_date,
    MAX(CASE WHEN l.field_id='refer_to'    THEN l.field_value END) AS refer_to,
    MAX(CASE WHEN l.field_id='body'        THEN l.field_value END) AS body,
    MAX(CASE WHEN l.field_id='refer_diag'  THEN l.field_value END) AS refer_diag,
    MAX(CASE WHEN l.field_id='reply_date'  THEN l.field_value END) AS reply_date,
    MAX(CASE WHEN l.field_id='reply_findings' THEN l.field_value END) AS reply_findings
  FROM transactions t
  LEFT JOIN lbt_data l ON l.form_id = t.id
  LEFT JOIN patient_data p ON p.pid = t.pid
  WHERE t.title = 'LBTref'
  GROUP BY t.id, t.pid, patient, t.groupname
) x
LEFT JOIN users u ON x.refer_to REGEXP '^[0-9]+$' AND u.id = CAST(x.refer_to AS UNSIGNED)
ORDER BY x.id
"""
# OpenEMR stores Refer To as a provider (user) id. We look up that provider's specialty.
# Older seed rows stored the specialty as plain text; those are passed through unchanged.
COLS = ["id", "pid", "patient", "groupname", "refer_date", "refer_to", "body", "refer_diag", "reply_date", "reply_findings"]


def fetch():
    cmd = ["docker", "exec", "-i", CONTAINER, "mariadb", "-u", DB_USER, f"-p{DB_PASS}",
           DB_NAME, "-B", "-N", "-e", QUERY]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"Query failed:\n{out.stderr}")
    rows = []
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        parts += [""] * (len(COLS) - len(parts))
        rows.append({c: (None if v == "NULL" else v) for c, v in zip(COLS, parts)})
    return rows


def parse(s):
    """ISO date or None. Never raises."""
    try:
        return date.fromisoformat((s or "").strip()[:10]) if (s or "").strip() else None
    except ValueError:
        return None


def diagnose(r, asof):
    """Return (primary_cause, days_since_referral, [other_issues])."""
    issues = []
    raw_ref, raw_rep = (r.get("refer_date") or "").strip(), (r.get("reply_date") or "").strip()
    ref, rep = parse(raw_ref), parse(raw_rep)
    findings = (r.get("reply_findings") or "").strip()

    if raw_ref and not ref or raw_rep and not rep:
        issues.append("date_problem")           # unreadable date
    elif ref and ref > asof:
        issues.append("date_problem")           # referral dated in the future
    elif ref and rep and rep < ref:
        issues.append("date_problem")           # reply before referral

    if not ref and not raw_ref:
        issues.append("missing_data")           # no referral date at all
    if not (r.get("body") or "").strip() or not (r.get("refer_diag") or "").strip():
        issues.append("missing_data")

    age = (asof - ref).days if ref else 0
    if raw_rep and not findings and "date_problem" not in issues:
        issues.append("reply_empty")
    if not raw_rep and ref and age > NO_REPLY_GRACE_DAYS and "date_problem" not in issues:
        issues.append("no_reply")

    # priority: bad dates make everything else unreliable, so they come first
    order = ["date_problem", "missing_data", "reply_empty", "no_reply"]
    issues = [c for c in order if c in issues]
    if issues:
        return issues[0], age, issues[1:]
    return ("closed" if raw_rep else "in_progress"), age, []


def days_label(x, asof):
    """Days since referral, or '?' if the date is unreadable, 'future' if after asof."""
    ref = parse(x.get("refer_date"))
    if ref is None:
        return "?"
    return "future" if ref > asof else str(x["age"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=date.today().isoformat())
    ap.add_argument("--score", action="store_true", help="grade seeded DIAG-TEST rows")
    a = ap.parse_args()
    asof = date.fromisoformat(a.asof)

    rows = fetch()
    results = []
    for r in rows:
        cause, age, also = diagnose(r, asof)
        owner, action = OWNERS[cause]
        results.append(dict(r, cause=cause, age=age, also=also, owner=owner, action=action))

    flagged = sorted((x for x in results if x["cause"] not in ("in_progress", "closed")),
                     key=lambda x: -x["age"])
    print(f"As of {asof}: {len(results)} referrals, {len(flagged)} need action\n")
    print(f"{'ID':>3} {'PID':>4} {'Days':>6}  {'Cause':<13} {'Owner':<22} {'Action':<50} Also")
    for x in flagged:
        print(f"{x['id']:>3} {x['pid']:>4} {days_label(x, asof):>6}  {x['cause']:<13} {x['owner']:<22} {x['action']:<50} {','.join(x['also'])}")

    if a.score:
        seeded = [x for x in results if (x["groupname"] or "").startswith("DIAG-TEST:")]
        norm = lambda s: s.replace("replied", "closed")
        misses = [(x["id"], x["groupname"].split(":")[1], x["cause"]) for x in seeded
                  if norm(x["groupname"].split(":")[1]) != x["cause"]]
        print(f"\nScore: {len(seeded) - len(misses)}/{len(seeded)} correct (seeded DIAG-TEST rows)")
        for m in misses:
            print(f"  MISS id {m[0]}: truth={m[1]}, diagnosed={m[2]}")

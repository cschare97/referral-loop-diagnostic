"""
explain_referrals.py - plain-language explanations for stalled referrals.

Division of labor (this is the point of the design):
    RULES   decide the cause AND the follow-up task (deterministic, always correct for the cause).
    MODEL   only writes a short explanation, and a checker rejects anything that contradicts the facts.
    If the model's text is rejected or the model is unreachable, a plain sentence built from the
    same facts is used instead, so the report is always complete.

Privacy: patient names are NEVER sent to a model. It sees internal PID, specialty, dates,
and which fields are blank. (All synthetic test data for now; keep this property if it is
ever pointed at real data, and use a local model or a BAA-covered setup before doing so.)

Backends:
    claude (default)  needs ANTHROPIC_API_KEY. Facts go to Anthropic's API.
    ollama            runs on your Mac via Ollama. Nothing leaves the machine.
Usage:
    python3 explain_referrals.py --asof 2026-10-20 --csv explained.csv              # rules only (default)
    python3 explain_referrals.py --asof 2026-10-20 --dry-run                        # show what a model would see
    python3 explain_referrals.py --asof 2026-10-20 --backend ollama --model qwen2.5:7b --csv explained.csv
"""
import argparse
import csv
import json
import os
import re
import urllib.error
import urllib.request
from datetime import date

from diagnose_openemr import fetch, diagnose, OWNERS, days_label, parse, NO_REPLY_GRACE_DAYS

MODEL = os.environ.get("EXPLAIN_MODEL", "claude-sonnet-5-5")

SYSTEM = (
    "You help front-desk and medical-assistant staff understand stalled referrals in an EHR. "
    "A rules engine has ALREADY decided the cause and the follow-up task; do not change or restate them. "
    "Write 1-2 plain sentences that DESCRIBE the problem. Use ONLY the facts provided: no invented names, "
    "dates, or steps, and no medical advice. "
    "Include days_since_referral and days_past_allowed_wait when they are numbers; they are different "
    "(time since the referral vs. time beyond the allowed wait). "
    "If date_issue is given, describe exactly that and nothing else. "
    "Name exactly which fields are blank (blank_fields); never write 'and/or'. "
    "Do not give instructions or use words like please, check, verify, or ensure. "
    "Do not mention things that are not problems, and do not repeat internal labels."
)

TOOL = {
    "name": "report",
    "description": "Return the explanation for one stalled referral.",
    "input_schema": {
        "type": "object",
        "properties": {
            "explanation": {"type": "string",
                            "description": "1-2 plain sentences describing what is wrong and for how long."},
        },
        "required": ["explanation"],
    },
}


# ---------------------------------------------------------------- facts
def facts_for(x, asof):
    """The only information a model sees. No patient name."""
    blank = []
    if not (x.get("body") or "").strip():
        blank.append("reason for referral")
    if not (x.get("refer_diag") or "").strip():
        blank.append("diagnosis")
    ref, rep_ = parse(x.get("refer_date")), parse(x.get("reply_date"))
    raw_ref, raw_rep = (x.get("refer_date") or "").strip(), (x.get("reply_date") or "").strip()
    if raw_ref and not ref:
        date_issue = f"the referral date is not in a readable format: {raw_ref!r}"
    elif raw_rep and not rep_:
        date_issue = f"the reply date is not in a readable format: {raw_rep!r}"
    elif ref and ref > asof:
        date_issue = "the referral date is in the future"
    elif ref and rep_ and rep_ < ref:
        date_issue = (f"the reply date ({rep_}) is before the referral date ({ref}); "
                      "we cannot tell which date is wrong")
    else:
        date_issue = ""
    past_wait = None
    if ref and ref <= asof and not raw_rep:
        past_wait = max(0, (asof - ref).days - NO_REPLY_GRACE_DAYS)
    return {
        "referral_id": x["id"],
        "patient_pid": x["pid"],
        "specialty": x.get("refer_to") or "unknown",
        "referral_date": x.get("refer_date") or "none on file",
        "days_since_referral": days_label(x, asof),
        "days_past_allowed_wait": past_wait,
        "date_issue": date_issue,
        "reply_date": x.get("reply_date") or "none on file",
        "blank_fields": blank,
        "cause": x["cause"],
        "other_problems": x["also"],
        "owner": x["owner"],
    }


# ---------------------------------------------------------------- rule-built text
def _join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _office(f):
    return "the specialist's office" if f["specialty"] == "unknown" else f"the {f['specialty']} office"


def _missing(f):
    items = list(f["blank_fields"])
    if f["referral_date"] == "none on file":
        items.append("referral date")
    return items


def plain_task(f):
    """Deterministic follow-up task for the owner. Always matches the cause."""
    c = f["cause"]
    if c == "no_reply":
        return f"Follow up with {_office(f)} for the visit note or result."
    if c == "missing_data":
        return f"Fill in the missing {_join(_missing(f))}."
    if c == "reply_empty":
        return f"Get the findings from {_office(f)} and record them."
    if c == "date_problem":
        issue = f["date_issue"]
        if "readable format" in issue:
            return "Look up the correct date in the source record and re-enter it as YYYY-MM-DD."
        if "future" in issue:
            return "Look up the correct referral date in the source record and fix it."
        return "Look at both dates in the source record and correct whichever is wrong."
    return OWNERS[c][1]


def plain_explanation(f):
    """Deterministic explanation built only from the facts. Used when the model's text is rejected."""
    c, days = f["cause"], f["days_since_referral"]
    numeric = str(days).isdigit()
    if c == "no_reply":
        s = f"No reply from {f['specialty']} is on file, {days} days after the referral"
        if f["days_past_allowed_wait"]:
            n = f["days_past_allowed_wait"]
            s += f" ({n} day{'' if n == 1 else 's'} past the allowed wait)"
        return s + "."
    if c == "missing_data":
        s = f"The referral is missing its {_join(_missing(f))}."
        if "no_reply" in f["other_problems"] and numeric:
            s += f" There is also no reply on file after {days} days."
        return s
    if c == "reply_empty":
        return f"A reply was logged on {f['reply_date']} but the findings are blank, so there is no usable result."
    if c == "date_problem":
        d = f["date_issue"]
        return d[:1].upper() + d[1:] + "."
    return OWNERS[c][1]


# ---------------------------------------------------------------- model backends
def _user_msg(facts):
    return "Referral facts:\n" + json.dumps(facts, indent=2)


def _ollama_url(raw):
    """OLLAMA_HOST is often set for the server in forms like '0.0.0.0' or 'host:port'.
    Turn any of those into a URL a client can call."""
    raw = (raw or "").strip() or "localhost:11434"
    if "://" not in raw:
        raw = "http://" + raw
    scheme, rest = raw.split("://", 1)
    host, _, tail = rest.partition("/")
    name, _, port = host.partition(":")
    if name in ("0.0.0.0", "", "::"):
        name = "localhost"                      # a bind address, not somewhere to connect
    return f"{scheme}://{name}:{port or '11434'}"


OLLAMA_HOST = _ollama_url(os.environ.get("OLLAMA_HOST"))


def _parse_explanation(content):
    snippet = " ".join(str(content).split())[:300]
    try:
        out = json.loads(content)
    except ValueError:
        raise ValueError(f"reply was not valid JSON: {snippet!r}")
    if isinstance(out, dict) and str(out.get("explanation") or "").strip():
        return str(out["explanation"]).strip()
    raise ValueError(f"reply missing explanation: {snippet!r}")


def ask_ollama(model, facts, host=OLLAMA_HOST):
    body = json.dumps({
        "model": model, "stream": False,
        "format": TOOL["input_schema"],
        "options": {"temperature": 0.2},
        "messages": [{"role": "system", "content": SYSTEM + " Reply with JSON only."},
                     {"role": "user", "content": _user_msg(facts)}],
    }).encode()
    req = urllib.request.Request(f"{host}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return _parse_explanation(json.loads(resp.read())["message"]["content"])


def ask(client, facts):
    resp = client.messages.create(
        model=MODEL, max_tokens=300, system=SYSTEM,
        tools=[TOOL], tool_choice={"type": "tool", "name": "report"},
        messages=[{"role": "user", "content": _user_msg(facts)}],
    )
    for block in resp.content:
        if getattr(block, "type", "") == "tool_use" and str(block.input.get("explanation") or "").strip():
            return block.input["explanation"].strip()
    raise ValueError("model returned no usable explanation")


# ---------------------------------------------------------------- checker
def validate(explanation, facts):
    """Reject text that contradicts or goes beyond the facts. Raises ValueError -> caller falls back."""
    text, low = explanation, explanation.lower()
    allowed = set(re.findall(r"\d+", json.dumps(facts)))
    extra = [n for n in re.findall(r"\d+", text) if n not in allowed]
    if extra:
        raise ValueError(f"number(s) not in the facts: {extra}")
    for n in re.findall(r"(\d+)\s+days?\s+(?:past|beyond|over)\b", text):
        if str(facts.get("days_past_allowed_wait")) != n:
            raise ValueError(f"'{n} days past the wait' does not match days_past_allowed_wait")
    if "future" in low and "future" not in (facts.get("date_issue") or ""):
        raise ValueError("says 'future' but the date is not in the future")
    if "and/or" in low and facts.get("blank_fields"):
        raise ValueError("vague 'and/or' when the blank fields are known")
    if "date issue" in low and not facts.get("date_issue"):
        raise ValueError("mentions a date issue that does not exist")
    if re.search(r"\b(please|check|verify|ensure)\b", low):
        raise ValueError("gives instructions; the task is handled separately")
    if re.search(r"\bno_reply\b|\bmissing_data\b|\bdate_problem\b|\breply_empty\b", text):
        raise ValueError("repeats an internal label")
    owner = (facts.get("owner") or "").lower()
    if owner and owner != "-" and owner in low:
        raise ValueError("mentions the owner's role (blames or confuses who must act)")
    if facts.get("reply_date") not in (None, "", "none on file") and re.search(
            r"\b(no|not received an?|without an?)\s+(reply|response)\b|\bhas not received\b|\bnot (been )?(replied|answered|responded)", low):
        raise ValueError("says there is no reply but a reply date is on file")
    if "allowed wait" in low and facts.get("days_past_allowed_wait") is None:
        raise ValueError("claims about the allowed wait without supporting facts")
    if re.search(r"\bthe (cause|task)\b|\bcause is\b|\bmarked as\b|\bthe owner\b", low):
        raise ValueError("talks about the system's own labels")
    if re.search(r"\b(cannot|can't|will not|won't)\s+(proceed|be processed|move forward)\b", low):
        raise ValueError("invents a consequence")
    if facts["cause"] == "no_reply" and str(facts["days_since_referral"]) not in text:
        raise ValueError("leaves out how long the referral has been waiting")
    return explanation


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=date.today().isoformat())
    ap.add_argument("--limit", type=int, default=0, help="only the first N (oldest first)")
    ap.add_argument("--dry-run", action="store_true", help="print the facts that would be sent; no model call")
    ap.add_argument("--no-model", action="store_true", help="rules only: skip the model entirely")
    ap.add_argument("--csv", help="write results to this CSV")
    ap.add_argument("--backend", choices=["claude", "ollama"], default=None,
                    help="optional: let a model write the explanation. Omit for rules only (the default)")
    ap.add_argument("--model", help="model name (ollama: must match `ollama list`)")
    a = ap.parse_args()
    asof = date.fromisoformat(a.asof)

    results = []
    for r in fetch():
        cause, age, also = diagnose(r, asof)
        if cause in ("in_progress", "closed"):
            continue
        owner, action = OWNERS[cause]
        results.append(dict(r, cause=cause, age=age, also=also, owner=owner, action=action))
    results.sort(key=lambda x: -x["age"])
    if a.limit:
        results = results[: a.limit]

    client = None
    use_model = a.backend is not None and not (a.dry_run or a.no_model)
    if use_model and a.backend == "ollama":
        if not a.model:
            raise SystemExit("Pass --model <name> (run `ollama list` to see what you have).")
    elif use_model:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit("Set ANTHROPIC_API_KEY first (or use --backend ollama / --no-model).")
        import anthropic
        client = anthropic.Anthropic()

    rows = []
    for x in results:
        facts = facts_for(x, asof)
        if a.dry_run:
            print(json.dumps(facts, indent=2), "\n")
            continue
        task, source, note = plain_task(facts), "rules", ""
        explanation = plain_explanation(facts)
        if use_model:
            try:
                text = ask_ollama(a.model, facts) if a.backend == "ollama" else ask(client, facts)
                explanation, source = validate(text, facts), "model"
            except Exception as e:
                note = f"(model text not used: {type(e).__name__}: {str(e)[:200]})"
        print(f"#{x['id']} [{x['cause']}] owner: {x['owner']}  [{source}] {note}\n  {explanation}\n  TASK: {task}\n")
        rows.append(dict(id=x["id"], pid=x["pid"], cause=x["cause"], owner=x["owner"],
                         explanation=explanation, followup_task=task, source=source, note=note))

    if a.csv and rows:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {len(rows)} rows to {a.csv}")

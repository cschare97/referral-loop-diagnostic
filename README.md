# Referral Loop Diagnostic

Finds referrals that have stalled in an OpenEMR database, says *why* each one is stuck,
who needs to act, and what the follow-up task is.

Most tools tell you a referral is "open." This one tells you it has had no reply from
Cardiology for 111 days, that it is 81 days past the allowed wait, and that the referral
coordinator should follow up with the Cardiology office.

> **Test data only.** Everything here was built and tested on synthetic data in a local
> development database. Do not point it at real patient data without a proper security and
> privacy review.

## What it does

It reads OpenEMR's native referral records (`transactions` + `lbt_data`, title `LBTref`) and
puts each referral in one state:

| State | Meaning | Owner | Task |
|---|---|---|---|
| `date_problem` | A date is unreadable, in the future, or the reply is dated before the referral | Ordering staff | Look up the correct date in the source record and fix it |
| `missing_data` | Reason for referral, diagnosis, or referral date is blank | Ordering staff | Fill in the missing fields |
| `reply_empty` | A reply date is logged but the findings are blank | Referral coordinator | Get the findings from the specialist's office |
| `no_reply` | No reply on file after more than 30 days | Referral coordinator | Follow up with the specialist's office |
| `in_progress` | Recent and still within normal time | — | None |
| `closed` | Reply on file with findings | — | None |

If a referral has more than one problem, the most urgent one is the main cause and the rest
are listed under **Also**. Priority is: `date_problem` > `missing_data` > `reply_empty` > `no_reply`.
Bad dates come first because they make every other check unreliable.

Output is sorted with the longest-waiting referrals first.

## Example

```
As of 2026-10-20: 31 referrals, 19 need action

 ID  PID   Days  Cause         Owner                  Action                          Also
  8    3    113  no_reply      Referral coordinator   Contact specialist for ...
 25    5     92  missing_data  Ordering staff         Add reason for referral ...     no_reply
 22    2     40  date_problem  Ordering staff         Correct the referral/reply date
 21    1      ?  date_problem  Ordering staff         Correct the referral/reply date
 23    3 future  date_problem  Ordering staff         Correct the referral/reply date
```

And with `explain_referrals.py`:

```
#8 [no_reply] owner: Referral coordinator  [rules]
  No reply from Gastroenterology is on file, 113 days after the referral (83 days past the allowed wait).
  TASK: Follow up with the Gastroenterology office for the visit note or result.
```

## Setup

Requires Python 3 and a running OpenEMR development stack in Docker. No extra Python packages
are needed for the diagnostic itself.

Database access goes through `docker exec` into the database container. Set these three
values at the top of `diagnose_openemr.py` to match your environment:

```python
CONTAINER = "development-easy-mysql-1"
DB_USER, DB_PASS, DB_NAME = "root", "root", "openemr"
```

Those are the defaults of a local development stack. Never reuse them anywhere real.

## Usage

```bash
# 1. Load synthetic test referrals into your DEV database (31 rows, all tagged DIAG-TEST)
docker exec -i <db-container> mariadb -u root -proot openemr < seed_openemr_referrals.sql
docker exec -i <db-container> mariadb -u root -proot openemr < seed_edge_cases.sql

# 2. Find stalled referrals
python3 diagnose_openemr.py --asof 2026-10-20

# 3. Same, and check it against the seeded answer key
python3 diagnose_openemr.py --asof 2026-10-20 --score

# 4. Add plain-language explanations and follow-up tasks
python3 explain_referrals.py --asof 2026-10-20 --csv explained.csv

# 5. Remove all test rows when you are done
docker exec -i <db-container> mariadb -u root -proot openemr < cleanup_test_referrals.sql
```

`--asof` sets the reference date. Use it to get repeatable results on test data.

## How OpenEMR stores referrals

Found from OpenEMR's published table documentation and checked against a running instance:

- `transactions` holds one row per referral (id, date, title, pid, user, groupname, authorized).
- `lbt_data` holds the details as key/value rows (`form_id` → `transactions.id`, `field_id`, `field_value`).
- The fields used here: `refer_date`, `refer_to`, `refer_from`, `body` (reason), `refer_diag`,
  `reply_date`, `reply_findings`.

## What it does not do

Be clear about the limits before relying on it.

- **OpenEMR has no native field for prior authorization, scheduling, or provider review of a
  reply.** So this tool cannot detect "authorization denied," "never scheduled," or "result not
  reviewed." It also cannot tell "never scheduled" apart from "visit happened, nothing came back";
  both show as `no_reply`. Closing those gaps would need data from other systems.
- **The 30-day "no reply" cutoff is a judgment call**, not a published standard. Change
  `NO_REPLY_GRACE_DAYS` in `diagnose_openemr.py`.
- **All testing used synthetic data that I wrote, with rules that I also wrote.** The `--score`
  result (31/31) shows the code does what it was written to do. It does not show the tool is
  accurate on real referral data, where problems are messier.
- It reads only. It never changes referral records.

## The optional model layer

`explain_referrals.py` separates the work on purpose:

- **Rules** decide the cause *and* the follow-up task. This is deterministic.
- **A model is optional** and only writes the explanation. It is off unless you pass `--backend`.
- A **checker** rejects model text that contradicts the facts (wrong numbers, blaming the wrong
  role, claiming no reply when one is on file, inventing consequences, giving instructions). A
  rejected explanation is replaced by a sentence built from the facts.

Why it is optional: in testing with a local 7B model, 19 explanations were reviewed by hand against
the facts and several had real errors that the first version of the checker missed. The
rule-built text had none. Every checker rule was added after seeing the model make that mistake,
so a new kind of mistake could still get through. Treat model text as a draft.

```bash
python3 explain_referrals.py --asof 2026-10-20 --dry-run                         # show what a model would see
python3 explain_referrals.py --asof 2026-10-20 --backend ollama --model <name>   # local model, nothing leaves your machine
python3 explain_referrals.py --asof 2026-10-20 --backend claude                  # needs ANTHROPIC_API_KEY
```

**Privacy:** patient names are never sent to a model, only the internal patient ID, specialty,
dates, and which fields are blank. This was checked in testing.

**Tested:** the Ollama backend with one model (`qwen2.5:7b`). **Not tested:** the Claude backend
against the live API.

## Files

| File | Purpose |
|---|---|
| `diagnose_openemr.py` | Reads OpenEMR referrals, finds stalled ones, names cause and owner |
| `explain_referrals.py` | Explanations and follow-up tasks; optional model layer with a checker |
| `seed_openemr_referrals.sql` | 20 synthetic referrals: missing data, no reply, in progress, replied |
| `seed_edge_cases.sql` | 11 awkward cases: bad dates, blank fields, same patient twice, 30/31-day boundary |
| `cleanup_test_referrals.sql` | Removes every `DIAG-TEST` row |
| `seed_referrals.py`, `diagnose_referrals.py` | Earlier standalone prototype on a small SQLite database, with six causes including prior authorization and scheduling that OpenEMR does not track |

## Testing notes

- 31 seeded referrals (20 ordinary + 11 edge cases), each tagged with the expected result in
  `transactions.groupname` (`DIAG-TEST:<state>`). The tag is read only by `--score`, never by the
  diagnosis itself.
- Edge cases found real bugs in the first version: a malformed date crashed the whole report, a
  reply dated before its referral was marked closed, and a future-dated referral was marked in
  progress.

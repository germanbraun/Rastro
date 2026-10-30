# deploy-customer: real runs on the demo machine (2026-10-29)

Evidence, not expected values. Details in `docs/decisions.md`.

- **install.sh energia** with a copy of `.env`: the users and the login took effect (401 without the login, 200 with
  it, Streamlit's WebSocket through the proxy: 101); a second run added nothing. The demo's other Ontop services,
  still on the laptop settings, were flagged ❌ by `check.py`, as they should.
- **check.py:** 31 of 32 ✅; the ❌ was true: the demo `.env` keeps the default database owner password, which only a
  new database (or an `ALTER ROLE`) changes.
- **backup.sh:** 48 s and 305 MB for a 3.2 GB database. **restore.sh --check:** 129 of 129 tables and 187 of 187 load
  records in 1 min 42 s, and the temporary database dropped.
- **upgrade.sh** in throwaway clones: a new version merged with a customer's confirmed correction (backup, local
  commit, merge); a change to the same correction from both sides stopped it and left everything as it was.
- **check_domain.py** as the read-only users: every section of oil and gas opened (4 business, 7 technical).
- **2026-10-30, after an audit:** `restore.sh` starts what it stopped even when `pg_restore` fails (tested with a
  stand-in for docker, `tests/test_restore_script.py`); on the demo machine `check.py` now says in one sentence that
  `.env` lacks the customer passwords, instead of a trace.

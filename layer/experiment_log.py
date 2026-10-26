"""The experiment log, written by commands instead of by hand (docs/experiments/<domain>.yaml).

A step's agent hours are the sum of its sessions' intervals minus their pauses, never typed. lint_errors() is the
structural check that can run at any time; method.py's --check adds the completeness check for closing.
"""
from datetime import datetime, timezone

import yaml

SESSION_FIELDS = ("started_on", "ended_on", "pauses", "work")
APPENDS = {"intervention": ("interventions", ("step", "decision", "reason", "kind", "minutes")),
           "error": ("errors_caught", ("step", "check", "failure_kind", "fix")),
           "method-change": ("method_changes", ("change", "scope", "reason"))}


class StrictLoader(yaml.SafeLoader):
    """A YAML loader that refuses duplicate keys: PyYAML silently keeps the last value."""


def _mapping(loader, node, deep=False):
    keys = [loader.construct_object(key, deep=deep) for key, _ in node.value]
    duplicates = sorted({str(k) for k in keys if keys.count(k) > 1})
    if duplicates:
        raise yaml.constructor.ConstructorError(None, None, f"duplicate keys {duplicates}", node.start_mark)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                             lambda loader, node: _mapping(loader, node, deep=True))


def load(path):
    return yaml.load(path.read_text(), Loader=StrictLoader) or {}


def save(path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=118))


def when(value):
    moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def session_hours(session):
    total = when(session["ended_on"]) - when(session["started_on"])
    for pause in session.get("pauses") or []:
        total -= when(pause["ended_on"]) - when(pause["started_on"])
    return total.total_seconds() / 3600


def step_hours(entry):
    return round(sum(session_hours(s) for s in entry.get("sessions", []) if s.get("ended_on")), 2)


def lint_errors(data, closing=False):
    """Structure that must hold at any moment: sessions well formed, at most one open (none when closing), no
    overlaps between any two sessions, and each step's agent hours equal to its intervals."""
    errors, intervals, open_sessions = [], [], []
    for name, entry in (data.get("steps") or {}).items():
        for n, session in enumerate(entry.get("sessions") or []):
            label = f"{name} session {n + 1}"
            missing = [f for f in ("started_on", "pauses", "work") if f not in session]
            if missing:
                errors.append(f"{label}: missing {missing}")
                continue
            try:
                start = when(session["started_on"])
                end = when(session["ended_on"]) if session.get("ended_on") else None
                pauses = [(when(p["started_on"]), when(p["ended_on"])) for p in session.get("pauses") or []]
            except (KeyError, TypeError, ValueError) as error:
                errors.append(f"{label}: unreadable time ({error})")
                continue
            if end is None:
                open_sessions.append(label)
                continue
            if end <= start:
                errors.append(f"{label}: ends before it starts")
            if any(not (start <= a < b <= end) for a, b in pauses):
                errors.append(f"{label}: a pause is outside its session")
            intervals.append((start, end, label))
        if entry.get("sessions") and entry.get("agent_hours") != step_hours(entry):
            errors.append(f"{name}: agent_hours {entry.get('agent_hours')} differ from its sessions ({step_hours(entry)})")
    if len(open_sessions) > (0 if closing else 1):
        errors.append(f"open sessions: {open_sessions}")
    intervals.sort()
    errors += [f"{a[2]} overlaps {b[2]}" for a, b in zip(intervals, intervals[1:]) if b[0] < a[1]]
    return errors


def start(data, step, at=None):
    if any(not s.get("ended_on") for e in (data.get("steps") or {}).values() for s in e.get("sessions") or []):
        raise ValueError("A session is still open: stop it first")
    entry = data.setdefault("steps", {}).setdefault(step, {"status": "in_progress", "evidence": []})
    entry.setdefault("sessions", []).append({"started_on": at or now(), "ended_on": None, "pauses": [], "work": ""})
    entry["agent_hours"] = step_hours(entry)
    entry.setdefault("human_hours", None)
    if not data.get("started_on"):
        data["started_on"] = entry["sessions"][-1]["started_on"]


def stop(data, step, work, at=None, status=None, evidence=()):
    """Close the step's open session; optionally set the step's status and add evidence lines."""
    sessions = (data.get("steps") or {}).get(step, {}).get("sessions") or []
    if not sessions or sessions[-1].get("ended_on"):
        raise ValueError(f"No open session in {step}")
    if not work.strip():
        raise ValueError("Say what the session did (--work)")
    sessions[-1].update(ended_on=at or now(), work=work)
    entry = data["steps"][step]
    entry["agent_hours"] = step_hours(entry)
    if status:
        entry["status"] = status
    entry.setdefault("evidence", []).extend(evidence)


def append(data, kind, fields):
    key, required = APPENDS[kind]
    missing = [f for f in required if f not in fields]
    if missing:
        raise ValueError(f"{kind} requires {missing}")
    data.setdefault(key, []).append({f: fields[f] for f in required})

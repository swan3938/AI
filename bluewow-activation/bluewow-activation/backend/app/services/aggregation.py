from collections import defaultdict

def compute_overview(rows: list, roster_total: int | None = None):
    activated = len({m.get("employee_id") for m in rows})
    if roster_total is None:
        return {"total": activated, "activated": activated, "activation_rate": None}
    rate = 0.0
    if roster_total > 0:
        rate = round(activated / roster_total, 4)
    return {"total": roster_total, "activated": activated, "activation_rate": rate}

def compute_monthly(rows: list):
    by_month = defaultdict(int)
    for m in rows:
        ts = m.get("first_login_at")
        if ts and len(ts) >= 7:
            key = ts[:7]
            by_month[key] += 1
    out = []
    for month, cnt in sorted(by_month.items()):
        out.append({"month": month, "activated": cnt, "activation_rate": None})
    return out

def compute_subject(rows: list, scope_overall: bool):
    by_subject = defaultdict(int)
    for m in rows:
        s = m.get("subject") or "未定义"
        by_subject[s] += 1
    out = []
    total = sum(by_subject.values())
    for s, cnt in sorted(by_subject.items()):
        rate = 0.0
        if total > 0:
            rate = round(cnt / total, 4)
        item = {"subject": s, "count": cnt, "rate": rate}
        if not scope_overall:
            item["month"] = None
        out.append(item)
    return out

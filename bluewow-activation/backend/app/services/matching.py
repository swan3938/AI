from typing import List, Dict

def match_by_employee_id(roster: List[Dict], activation: List[Dict]) -> List[Dict]:
    index = {r.get("employee_id"): r for r in roster if r.get("employee_id")}
    out = []
    for a in activation:
        k = a.get("employee_id")
        r = index.get(k)
        if k and r:
            m = {**r, **a}
            out.append(m)
    return out

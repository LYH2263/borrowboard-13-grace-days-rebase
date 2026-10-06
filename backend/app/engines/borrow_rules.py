"""One active loan per item + overdue detection."""

from datetime import date

def can_lend(item_status: str, active_loans: int) -> dict:
    if item_status != "available":
        return {"ok": False, "reason": "item_not_available"}
    if active_loans > 0:
        return {"ok": False, "reason": "already_on_loan"}
    return {"ok": True, "reason": ""}

def is_overdue(due_date: str, today: str, loan_status: str, grace_days: int = 0) -> bool:
    """Overdue is computed on the fly: today must be past due_date + grace_days.

    due_date stays the string captured at lend time; grace only shifts the
    comparison. The loan is overdue strictly after the grace window, so the
    due date itself (and due+grace) still count as on time. Malformed dates
    are treated as not overdue. This is the single overdue entry point that
    board, loans and any future return-preview must share.
    """
    if loan_status != "active" or not due_date:
        return False
    try:
        due = date.fromisoformat(due_date)
        now = date.fromisoformat(today)
    except ValueError:
        return False
    return (now - due).days > int(grace_days)

def classify_loans(loans: list[dict], today: str, grace_days: int = 0) -> dict:
    active, overdue, returned = [], [], []
    for L in loans:
        st = L.get("status")
        if st == "returned":
            returned.append(L)
        elif is_overdue(L.get("due_date"), today, st, grace_days):
            overdue.append({**L, "overdue": True})
        elif st == "active":
            active.append({**L, "overdue": False})
    return {"active": active, "overdue": overdue, "returned": returned}

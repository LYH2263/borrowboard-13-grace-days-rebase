from app.engines.borrow_rules import can_lend, is_overdue, classify_loans

def test_mutex():
    assert can_lend("available", 0)["ok"]
    assert can_lend("available", 1)["reason"] == "already_on_loan"
    assert can_lend("retired", 0)["ok"] is False

def test_overdue():
    assert is_overdue("2020-01-01", "2026-01-01", "active")
    assert not is_overdue("2020-01-01", "2026-01-01", "returned")

def test_grace_boundary():
    due = "2026-01-01"
    # due date itself and due+grace are still on time; due+grace+1 is overdue
    assert not is_overdue(due, "2026-01-01", "active", 3)
    assert not is_overdue(due, "2026-01-04", "active", 3)
    assert is_overdue(due, "2026-01-05", "active", 3)
    # grace=0 keeps the old on-the-fly semantics
    assert not is_overdue(due, "2026-01-01", "active")
    assert is_overdue(due, "2026-01-02", "active")
    # returned loans never become overdue regardless of grace
    assert not is_overdue("2020-01-01", "2026-01-01", "returned", 0)

def test_grace_moves_seed_loan_back_to_active():
    # the checked-out seed sample (due 2020-06-01) may migrate out of overdue
    # purely by widening grace; its due_date string is never rewritten
    assert is_overdue("2020-06-01", "2026-10-06", "active")
    assert not is_overdue("2020-06-01", "2026-10-06", "active", 100000)
    loans = [{"id": 4, "status": "active", "due_date": "2020-06-01"}]
    wide = classify_loans(loans, "2026-10-06", 100000)
    assert len(wide["active"]) == 1 and wide["active"][0]["overdue"] is False
    assert wide["overdue"] == []
    tight = classify_loans(loans, "2026-10-06", 0)
    assert len(tight["overdue"]) == 1 and tight["active"] == []

def test_malformed_due_date_not_overdue():
    assert not is_overdue("abc", "2026-01-01", "active", 0)
    assert not is_overdue("", "2026-01-01", "active", 0)

def test_classify():
    r = classify_loans([
        {"id": 1, "status": "active", "due_date": "2020-01-01"},
        {"id": 2, "status": "active", "due_date": "2099-01-01"},
        {"id": 3, "status": "returned", "due_date": "2020-01-01"},
    ], "2026-01-01")
    assert len(r["overdue"]) == 1 and len(r["active"]) == 1 and len(r["returned"]) == 1

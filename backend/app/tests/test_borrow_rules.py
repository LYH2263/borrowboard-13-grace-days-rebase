from app.engines.borrow_rules import can_lend, is_overdue, classify_loans, parse_grace_days

def test_mutex():
    assert can_lend("available", 0)["ok"]
    assert can_lend("available", 1)["reason"] == "already_on_loan"
    assert can_lend("retired", 0)["ok"] is False

def test_overdue():
    assert is_overdue("2020-01-01", "2026-01-01", "active")
    assert not is_overdue("2020-01-01", "2026-01-01", "returned")

def test_overdue_grace():
    # 应还 2020-06-01 + 宽限 5 天 → 2020-06-06 及以前不逾期,2020-06-07 起逾期
    assert not is_overdue("2020-06-01", "2020-06-06", "active", 5)
    assert is_overdue("2020-06-01", "2020-06-07", "active", 5)
    # 宽限 0 与旧行为一致
    assert is_overdue("2020-06-01", "2020-06-02", "active", 0)
    # 已还永不逾期
    assert not is_overdue("2020-06-01", "2030-01-01", "returned", 5)

def test_classify():
    r = classify_loans([
        {"id": 1, "status": "active", "due_date": "2020-01-01"},
        {"id": 2, "status": "active", "due_date": "2099-01-01"},
        {"id": 3, "status": "returned", "due_date": "2020-01-01"},
    ], "2026-01-01")
    assert len(r["overdue"]) == 1 and len(r["active"]) == 1 and len(r["returned"]) == 1

def test_classify_grace_flips_back():
    loans = [{"id": 1, "status": "active", "due_date": "2020-06-01"}]
    assert len(classify_loans(loans, "2020-06-07", 0)["overdue"]) == 1
    r = classify_loans(loans, "2020-06-07", 6)
    assert len(r["active"]) == 1 and r["active"][0]["overdue"] is False

def test_parse_grace_days():
    assert parse_grace_days(0) == 0
    assert parse_grace_days(7) == 7
    assert parse_grace_days("12") == 12
    assert parse_grace_days(-1) is None
    assert parse_grace_days(1.5) is None
    assert parse_grace_days("1.5") is None
    assert parse_grace_days("abc") is None
    assert parse_grace_days("") is None
    assert parse_grace_days(None) is None
    assert parse_grace_days(True) is None

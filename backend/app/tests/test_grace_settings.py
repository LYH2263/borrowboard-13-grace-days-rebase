import pytest
from pydantic import ValidationError

from app import seed
from app.db import connect
from app import main


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    # route functions open their own connections via db.db_path(), which reads
    # DATA_DIR lazily, so pointing it at a temp dir isolates the whole run.
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    seed.init_db()
    return tmp_path


def test_seed_loan_starts_overdue_everywhere(fresh_db):
    b = main.board()
    assert b["counts"]["overdue"] == 1 and b["counts"]["active"] == 0
    assert b["overdue"][0]["due_date"] == "2020-06-01"
    loans = main.loans()
    assert len(loans["overdue"]) == 1 and loans["active"] == []


def test_widening_grace_moves_loan_to_active_everywhere(fresh_db):
    main.set_grace_days(main.GraceDaysIn(grace_days=100000))
    # top bar + active column (board) and the records page (loans) move together
    b = main.board()
    assert b["counts"]["overdue"] == 0 and b["counts"]["active"] == 1
    assert b["active"][0]["due_date"] == "2020-06-01" and b["active"][0]["overdue"] is False
    loans = main.loans()
    assert loans["overdue"] == [] and len(loans["active"]) == 1
    # the stored due_date string is still the one captured at lend time
    assert loans["active"][0]["due_date"] == "2020-06-01"
    # narrowing grace back restores overdue, again in both endpoints
    main.set_grace_days(main.GraceDaysIn(grace_days=0))
    assert main.board()["counts"]["overdue"] == 1
    assert len(main.loans()["overdue"]) == 1


def test_invalid_grace_is_rejected_and_not_persisted(fresh_db):
    main.set_grace_days(main.GraceDaysIn(grace_days=5))
    with pytest.raises(ValidationError):
        main.GraceDaysIn(grace_days=-1)
    # a rejected model never reaches the DB: the stored value is unchanged
    c = connect()
    assert c.execute("SELECT value FROM settings WHERE key='grace_days'").fetchone()["value"] == "5"
    c.close()
    with pytest.raises(ValidationError):
        main.GraceDaysIn(grace_days=1.5)  # type: ignore[arg-type]


def test_get_grace_days_defaults_when_missing(fresh_db):
    c = connect()
    c.execute("DELETE FROM settings WHERE key='grace_days'")
    c.commit()
    assert main.get_grace_days(c) == 0
    c.close()

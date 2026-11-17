"""Unit tests for Phase 1: Data layer, generator, and CSV importer."""

import io
import json
import os
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models import Base, Ticket, User
from backend.app.services.importer import import_tickets_from_csv
from ml.seed_data import generate_synthetic_dataset, SEED


@pytest.fixture
def db_session():
    """In-memory SQLite database session fixture."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_synthetic_data_generator_reproducibility(tmp_path):
    """Verify synthetic dataset generation is reproducible with fixed seed."""
    csv_1 = tmp_path / "tickets_1.csv"
    rep_1 = tmp_path / "rep_1.json"
    csv_2 = tmp_path / "tickets_2.csv"
    rep_2 = tmp_path / "rep_2.json"

    # Generate 100 tickets twice
    t1, p1 = generate_synthetic_dataset(count=100, output_path=str(csv_1), report_path=str(rep_1))
    t2, p2 = generate_synthetic_dataset(count=100, output_path=str(csv_2), report_path=str(rep_2))

    assert len(t1) == 100
    assert len(t2) == 100
    assert t1[0]["ticket_id"] == t2[0]["ticket_id"]
    assert t1[0]["subject"] == t2[0]["subject"]
    assert p1["metadata"]["is_synthetic"] is True
    assert p1["metadata"]["total_tickets"] == 100


def test_data_splits_time_ordered(tmp_path):
    """Verify train/val/test splits are strictly time-ordered."""
    csv_path = tmp_path / "tickets.csv"
    rep_path = tmp_path / "profile.json"

    tickets, profile = generate_synthetic_dataset(count=200, output_path=str(csv_path), report_path=str(rep_path))

    # Parse timestamps
    created_ats = [t["created_at"] for t in tickets]
    assert created_ats == sorted(created_ats), "Tickets must be chronologically ordered"

    train_end = profile["splits"]["train"]["end"]
    val_start = profile["splits"]["validation"]["start"]
    val_end = profile["splits"]["validation"]["end"]
    test_start = profile["splits"]["test"]["start"]

    assert train_end <= val_start
    assert val_end <= test_start


def test_csv_importer_default_mapping(db_session):
    """Verify CSV importer works with standard columns."""
    sample_csv = """ticket_id,created_at,subject,body,category,priority,assigned_team,sla_hours
TCK-TEST-1,2026-01-01 10:00:00,VPN Issue,Cannot connect to VPN,Network/VPN,P2,Network Ops,8.0
TCK-TEST-2,2026-01-01 11:00:00,Password Reset,Forgot my password,Password/Access,P3,IT Helpdesk,24.0
"""
    imported, errors, err_list = import_tickets_from_csv(db_session, sample_csv)

    assert imported == 2
    assert errors == 0
    t1 = db_session.query(Ticket).filter_by(ticket_id="TCK-TEST-1").first()
    assert t1 is not None
    assert t1.category == "Network/VPN"
    assert t1.priority == "P2"
    assert t1.sla_hours == 8.0


def test_csv_importer_custom_mapping(db_session):
    """Verify CSV importer works with custom column headers."""
    custom_csv = """IncidentNum,OpenDate,Title,Details,Type,SeverityLevel,Group
INC-999,2026-02-15 14:00:00,Printer Jam,Tray 2 jammed,Printer,P4,IT Helpdesk
"""
    custom_mapping = {
        "IncidentNum": "ticket_id",
        "OpenDate": "created_at",
        "Title": "subject",
        "Details": "body",
        "Type": "category",
        "SeverityLevel": "priority",
        "Group": "assigned_team",
    }
    imported, errors, err_list = import_tickets_from_csv(db_session, custom_csv, custom_mapping=custom_mapping)

    assert imported == 1
    t = db_session.query(Ticket).filter_by(ticket_id="INC-999").first()
    assert t is not None
    assert t.subject == "Printer Jam"
    assert t.category == "Printer"
    assert t.priority == "P4"

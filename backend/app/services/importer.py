"""CSV Ingestion Service with flexible column mapping."""

import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.core.logging import logger
from backend.app.db.models import Ticket

DEFAULT_COLUMN_MAPPING = {
    "ticket_id": "ticket_id",
    "id": "ticket_id",
    "incident_id": "ticket_id",
    "created_at": "created_at",
    "opened_at": "created_at",
    "date": "created_at",
    "subject": "subject",
    "title": "subject",
    "short_description": "subject",
    "summary": "subject",
    "body": "body",
    "description": "body",
    "details": "body",
    "requester_id": "requester_id",
    "caller_id": "requester_id",
    "user_id": "requester_id",
    "department": "department",
    "dept": "department",
    "channel": "channel",
    "source": "channel",
    "category": "category",
    "issue_type": "category",
    "priority": "priority",
    "severity": "priority",
    "assigned_team": "assigned_team",
    "assignment_group": "assigned_team",
    "team": "assigned_team",
    "agent_id": "agent_id",
    "assignee": "agent_id",
    "first_response_at": "first_response_at",
    "resolved_at": "resolved_at",
    "closed_at": "resolved_at",
    "sla_hours": "sla_hours",
    "breached": "breached",
    "reopen_count": "reopen_count",
    "reopens": "reopen_count",
    "contact_count": "contact_count",
    "contacts": "contact_count",
    "escalated": "escalated",
    "status": "status",
    "state": "status",
}


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse string to datetime using ISO or standard date formats."""
    if not dt_str or dt_str.strip() == "" or dt_str.lower() in ("none", "null", "nan"):
        return None
    dt_str = dt_str.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    # Fallback to dateutil if available
    try:
        from dateutil.parser import parse
        return parse(dt_str)
    except Exception:
        return None


def parse_bool(val: Any) -> bool:
    """Parse truthy value to boolean."""
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() in ("true", "1", "yes", "y", "t")


def import_tickets_from_csv(
    db: Session,
    csv_file: io.StringIO | str,
    custom_mapping: Optional[Dict[str, str]] = None,
    batch_size: int = 1000,
) -> Tuple[int, int, List[str]]:
    """Import tickets from CSV stream or string with column mapping."""
    if isinstance(csv_file, str):
        reader = csv.DictReader(io.StringIO(csv_file))
    else:
        reader = csv.DictReader(csv_file)

    if not reader.fieldnames:
        return 0, 0, ["CSV file contains no headers or is empty."]

    # Combine custom mapping with defaults
    active_mapping: Dict[str, str] = {}
    for col in reader.fieldnames:
        clean_col = col.strip()
        lower_col = clean_col.lower()
        if custom_mapping and clean_col in custom_mapping:
            active_mapping[clean_col] = custom_mapping[clean_col]
        elif custom_mapping and lower_col in custom_mapping:
            active_mapping[clean_col] = custom_mapping[lower_col]
        elif lower_col in DEFAULT_COLUMN_MAPPING:
            active_mapping[clean_col] = DEFAULT_COLUMN_MAPPING[lower_col]

    imported_count = 0
    error_count = 0
    errors: List[str] = []
    tickets_to_insert: List[Ticket] = []

    existing_ids = {row[0] for row in db.query(Ticket.ticket_id).all()}

    for row_idx, row in enumerate(reader, start=1):
        try:
            mapped_data: Dict[str, Any] = {}
            for col_name, value in row.items():
                if col_name in active_mapping and value is not None:
                    target_field = active_mapping[col_name]
                    mapped_data[target_field] = value.strip()

            ticket_id = mapped_data.get("ticket_id") or f"TCK-IMP-{row_idx:05d}"
            if ticket_id in existing_ids:
                # Skip duplicate ticket_id
                continue

            subject = mapped_data.get("subject") or "No Subject"
            body = mapped_data.get("body") or subject

            created_at = parse_datetime(mapped_data.get("created_at")) or datetime.now(timezone.utc)
            resolved_at = parse_datetime(mapped_data.get("resolved_at"))
            first_response_at = parse_datetime(mapped_data.get("first_response_at"))

            priority = mapped_data.get("priority", "P3").upper()
            if priority not in ("P1", "P2", "P3", "P4"):
                priority = "P3"

            sla_hours = float(mapped_data.get("sla_hours") or (4.0 if priority == "P1" else 8.0 if priority == "P2" else 24.0 if priority == "P3" else 72.0))

            breached = parse_bool(mapped_data.get("breached"))
            if not breached and resolved_at and created_at:
                elapsed_hours = (resolved_at - created_at).total_seconds() / 3600.0
                breached = elapsed_hours > sla_hours

            ticket = Ticket(
                ticket_id=ticket_id,
                created_at=created_at,
                subject=subject,
                body=body,
                requester_id=mapped_data.get("requester_id") or f"USR-{row_idx:04d}",
                department=mapped_data.get("department") or "General",
                channel=mapped_data.get("channel") or "portal",
                category=mapped_data.get("category") or "Service Request",
                priority=priority,
                assigned_team=mapped_data.get("assigned_team") or "IT Helpdesk",
                agent_id=mapped_data.get("agent_id"),
                first_response_at=first_response_at,
                resolved_at=resolved_at,
                sla_hours=sla_hours,
                breached=breached,
                reopen_count=int(mapped_data.get("reopen_count") or 0),
                contact_count=int(mapped_data.get("contact_count") or 1),
                escalated=parse_bool(mapped_data.get("escalated")),
                status=mapped_data.get("status") or ("resolved" if resolved_at else "open"),
            )
            tickets_to_insert.append(ticket)
            existing_ids.add(ticket_id)

            if len(tickets_to_insert) >= batch_size:
                db.bulk_save_objects(tickets_to_insert)
                db.commit()
                imported_count += len(tickets_to_insert)
                tickets_to_insert = []

        except Exception as ex:
            error_count += 1
            if len(errors) < 10:
                errors.append(f"Row {row_idx}: {str(ex)}")

    if tickets_to_insert:
        db.bulk_save_objects(tickets_to_insert)
        db.commit()
        imported_count += len(tickets_to_insert)

    logger.info(f"CSV import completed: {imported_count} imported, {error_count} failed")
    return imported_count, error_count, errors

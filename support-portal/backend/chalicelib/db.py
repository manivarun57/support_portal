import os
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor

from chalicelib.logger import log_error, log_info

load_dotenv()


def _summarize_query(query: str) -> str:
    return " ".join(query.split())[:120]


@dataclass
class TicketRecord:
    id: str
    subject: str
    priority: str
    category: str
    description: str
    status: str
    user_id: str
    created_at: str
    attachment_url: Optional[str] = None


class DatabaseClient:
    """
    Lightweight database helper that can talk to PostgreSQL (default) or fall back to SQLite
    when RDS credentials are not provided. The behavior mirrors previous logic but now logs
    the major steps and failures.
    """

    def __init__(self) -> None:
        self._use_sqlite = bool(not os.getenv("DB_HOST"))
        self.placeholder = "?" if self._use_sqlite else "%s"
        if self._use_sqlite:
            db_dir = Path(__file__).resolve().parent
            self._sqlite_path = db_dir / "support-portal.db"
            log_info("Using SQLite fallback database", path=str(self._sqlite_path))
            self._ensure_sqlite_schema()
        else:
            self._dsn = {
                "host": os.getenv("DB_HOST"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "dbname": os.getenv("DB_NAME"),
            }
            log_info("Configured PostgreSQL connection", host=self._dsn["host"], db=self._dsn["dbname"])

    @contextmanager
    def connection(self):
        conn = None
        try:
            conn = self._connect_sqlite() if self._use_sqlite else self._connect_postgres()
            yield conn
        finally:
            if conn:
                conn.close()

    def _connect_sqlite(self):
        try:
            conn = sqlite3.connect(self._sqlite_path)
            conn.row_factory = sqlite3.Row
            log_info("SQLite connection opened")
            return conn
        except sqlite3.Error as exc:
            log_error("SQLite connection failed", error=str(exc))
            raise

    def _connect_postgres(self):
        try:
            conn = psycopg2.connect(cursor_factory=RealDictCursor, **self._dsn)
            log_info("PostgreSQL connection opened")
            return conn
        except OperationalError as exc:
            log_error("PostgreSQL connection failed", error=str(exc))
            raise

    def execute(self, query: str, params: Optional[Iterable[Any]] = None) -> None:
        statement = _summarize_query(query)
        try:
            with self.connection() as conn:
                cur = conn.cursor()
                cur.execute(query, list(params or []))
                conn.commit()
                log_info("Executed DB statement", statement=statement)
        except Exception as exc:
            log_error("DB execute failed", statement=statement, error=str(exc))
            raise

    def fetch_all(
        self, query: str, params: Optional[Iterable[Any]] = None
    ) -> List[Dict[str, Any]]:
        statement = _summarize_query(query)
        try:
            with self.connection() as conn:
                cur = conn.cursor()
                cur.execute(query, list(params or []))
                rows = cur.fetchall()
                log_info("Fetched rows", statement=statement, count=len(rows))
                if self._use_sqlite:
                    return [dict(row) for row in rows]
                return rows
        except Exception as exc:
            log_error("DB fetch_all failed", statement=statement, error=str(exc))
            raise

    def fetch_one(
        self, query: str, params: Optional[Iterable[Any]] = None
    ) -> Optional[Dict[str, Any]]:
        statement = _summarize_query(query)
        try:
            with self.connection() as conn:
                cur = conn.cursor()
                cur.execute(query, list(params or []))
                row = cur.fetchone()
                log_info("Fetched single row", statement=statement, found=bool(row))
                if row is None:
                    return None
                if self._use_sqlite:
                    return dict(row)
                return row
        except Exception as exc:
            log_error("DB fetch_one failed", statement=statement, error=str(exc))
            raise

    def _ensure_sqlite_schema(self) -> None:
        schema_statements = [
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                priority TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                attachment_url TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ticket_files (
                id TEXT PRIMARY KEY,
                ticket_id TEXT NOT NULL,
                file_url TEXT NOT NULL,
                file_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(ticket_id) REFERENCES tickets(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                ticket_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(ticket_id) REFERENCES tickets(id)
            )
            """,
        ]
        try:
            with self.connection() as conn:
                cur = conn.cursor()
                for statement in schema_statements:
                    cur.execute(statement)
                conn.commit()
            log_info("SQLite schema ensured")
        except Exception as exc:  # pragma: no cover - initialization guard
            log_error("Failed to bootstrap SQLite schema", error=str(exc))
            raise


class TicketRepository:
    def __init__(self) -> None:
        self.db = DatabaseClient()

    def create_ticket(
        self,
        *,
        subject: str,
        priority: str,
        category: str,
        description: str,
        user_id: str,
        attachment_url: Optional[str] = None,
    ) -> TicketRecord:
        ticket_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        query = f"""
            INSERT INTO tickets (id, subject, priority, category, description, status, user_id, created_at, attachment_url)
            VALUES ({', '.join([self.db.placeholder] * 9)})
        """
        params = [
            ticket_id,
            subject,
            priority,
            category,
            description,
            "open",
            user_id,
            now,
            attachment_url,
        ]
        self.db.execute(query, params)
        log_info("Ticket created", ticket_id=ticket_id, user_id=user_id)
        return TicketRecord(
            id=ticket_id,
            subject=subject,
            priority=priority,
            category=category,
            description=description,
            status="open",
            user_id=user_id,
            created_at=now,
            attachment_url=attachment_url,
        )

    def save_ticket_file(
        self, *, ticket_id: str, file_url: str, file_name: str
    ) -> None:
        query = f"""
            INSERT INTO ticket_files (id, ticket_id, file_url, file_name, created_at)
            VALUES ({', '.join([self.db.placeholder] * 5)})
        """
        self.db.execute(
            query,
            [
                str(uuid.uuid4()),
                ticket_id,
                file_url,
                file_name,
                datetime.now(timezone.utc).isoformat(),
            ],
        )
        log_info("Ticket attachment persisted", ticket_id=ticket_id, file_name=file_name)

    def list_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM tickets WHERE user_id = " + self.db.placeholder + " ORDER BY created_at DESC"
        records = self.db.fetch_all(query, [user_id])
        log_info("Fetched tickets for user", user_id=user_id, count=len(records))
        return records

    def get_ticket(self, ticket_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT * FROM tickets
            WHERE id = {placeholder} AND user_id = {placeholder}
        """.format(placeholder=self.db.placeholder)
        record = self.db.fetch_one(query, [ticket_id, user_id])
        log_info("Fetched ticket", ticket_id=ticket_id, found=bool(record))
        return record

    def get_metrics(self, user_id: str) -> Dict[str, int]:
        base_query = """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open,
                SUM(CASE WHEN status IN ('resolved', 'closed') THEN 1 ELSE 0 END) AS resolved
            FROM tickets
            WHERE user_id = {placeholder}
        """.format(placeholder=self.db.placeholder)
        row = self.db.fetch_one(base_query, [user_id]) or {"total": 0, "open": 0, "resolved": 0}
        metrics = {
            "total": row.get("total", 0) or 0,
            "open": row.get("open", 0) or 0,
            "resolved": row.get("resolved", 0) or 0,
        }
        log_info("Calculated metrics", user_id=user_id, **metrics)
        return metrics


class CommentRepository:
    def __init__(self) -> None:
        self.db = DatabaseClient()

    def list_for_ticket(self, ticket_id: str) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM comments
            WHERE ticket_id = {placeholder}
            ORDER BY created_at ASC
        """.format(placeholder=self.db.placeholder)
        rows = self.db.fetch_all(query, [ticket_id])
        log_info("Fetched comments", ticket_id=ticket_id, count=len(rows))
        return rows

    def seed_demo_comment(self, ticket_id: str, user_id: str) -> None:
        """
        Local helper to populate a placeholder comment the first time we create a ticket.
        """
        query = f"""
            INSERT INTO comments (id, ticket_id, user_id, comment, created_at)
            VALUES ({', '.join([self.db.placeholder] * 5)})
        """
        self.db.execute(
            query,
            [
                str(uuid.uuid4()),
                ticket_id,
                user_id,
                "Thanks for opening this ticket – we will get back to you shortly.",
                datetime.now(timezone.utc).isoformat(),
            ],
        )
        log_info("Seeded demo comment", ticket_id=ticket_id)


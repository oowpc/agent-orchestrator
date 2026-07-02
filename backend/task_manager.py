"""SQLite-backed task manager for the MVP.

This module intentionally uses Python's built-in sqlite3 module to keep the
first version lightweight and easy to run.

The schema is evidence-driven:
- tasks store the task package fields.
- evidence_packages store proof from worker agents.
- reviews store reviewer judgments.
- conflicts and decisions store escalation records.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.models import ConflictRecord, DecisionRecord, EvidencePackage, Plan, ReviewRecord


VALID_STATUSES = {
    "pending",
    "running",
    "reviewing",
    "testing",
    "needs_fix",
    "done",
    "failed",
    "blocked",
}

VALID_CONFLICT_STATUSES = {"open", "escalated", "resolved", "closed"}


TASK_EXTRA_COLUMNS = {
    "goal": "TEXT NOT NULL DEFAULT ''",
    "boundary": "TEXT NOT NULL DEFAULT ''",
    "input_materials_json": "TEXT NOT NULL DEFAULT '[]'",
    "tool_permissions_json": "TEXT NOT NULL DEFAULT '[]'",
    "deliverable_format": "TEXT NOT NULL DEFAULT ''",
    "evidence_requirements_json": "TEXT NOT NULL DEFAULT '[]'",
    "blocking_conditions_json": "TEXT NOT NULL DEFAULT '[]'",
    "decision_owner": "TEXT NOT NULL DEFAULT 'user'",
    "next_action": "TEXT NOT NULL DEFAULT ''",
}


class TaskManager:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    requirement TEXT NOT NULL,
                    worth_doing TEXT NOT NULL,
                    recommended_solution TEXT NOT NULL,
                    alternatives_json TEXT NOT NULL,
                    risks_json TEXT NOT NULL,
                    assumptions_json TEXT NOT NULL,
                    next_steps_json TEXT NOT NULL,
                    report_path TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    acceptance_criteria_json TEXT NOT NULL,
                    dependencies_json TEXT NOT NULL,
                    risks_json TEXT NOT NULL,
                    goal TEXT NOT NULL DEFAULT '',
                    boundary TEXT NOT NULL DEFAULT '',
                    input_materials_json TEXT NOT NULL DEFAULT '[]',
                    tool_permissions_json TEXT NOT NULL DEFAULT '[]',
                    deliverable_format TEXT NOT NULL DEFAULT '',
                    evidence_requirements_json TEXT NOT NULL DEFAULT '[]',
                    blocking_conditions_json TEXT NOT NULL DEFAULT '[]',
                    decision_owner TEXT NOT NULL DEFAULT 'user',
                    next_action TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(plan_id) REFERENCES plans(id)
                )
                """
            )
            self._ensure_task_columns(conn)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_events (
                    id TEXT PRIMARY KEY,
                    task_db_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_db_id) REFERENCES tasks(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id TEXT PRIMARY KEY,
                    task_db_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    token_usage INTEGER NOT NULL DEFAULT 0,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    FOREIGN KEY(task_db_id) REFERENCES tasks(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_packages (
                    id TEXT PRIMARY KEY,
                    task_db_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    completed_work TEXT NOT NULL,
                    evidence_locations_json TEXT NOT NULL,
                    commands_run_json TEXT NOT NULL,
                    changed_files_json TEXT NOT NULL,
                    risks_json TEXT NOT NULL,
                    suggested_next_steps_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_db_id) REFERENCES tasks(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    id TEXT PRIMARY KEY,
                    task_db_id TEXT NOT NULL,
                    reviewer_agent TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    issues_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    evidence_package_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(task_db_id) REFERENCES tasks(id),
                    FOREIGN KEY(evidence_package_id) REFERENCES evidence_packages(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conflicts (
                    id TEXT PRIMARY KEY,
                    task_db_id TEXT NOT NULL,
                    conflict_type TEXT NOT NULL,
                    agents_involved_json TEXT NOT NULL,
                    claims_json TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    decision_owner TEXT NOT NULL,
                    status TEXT NOT NULL,
                    final_decision TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(task_db_id) REFERENCES tasks(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    conflict_id TEXT NOT NULL,
                    decision_owner TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    evidence_refs_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(conflict_id) REFERENCES conflicts(id)
                )
                """
            )

    def _ensure_task_columns(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute("PRAGMA table_info(tasks)").fetchall()
        existing = {row["name"] for row in rows}
        for column, definition in TASK_EXTRA_COLUMNS.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {column} {definition}")

    def save_plan(self, plan: Plan, report_path: Path | None = None) -> str:
        plan_id = f"plan_{uuid4().hex[:12]}"
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO plans (
                    id, requirement, worth_doing, recommended_solution,
                    alternatives_json, risks_json, assumptions_json, next_steps_json,
                    report_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    plan.requirement,
                    plan.worth_doing,
                    plan.recommended_solution,
                    _json(plan.alternatives),
                    _json(plan.risks),
                    _json(plan.assumptions),
                    _json(plan.next_steps),
                    str(report_path) if report_path else None,
                    now,
                ),
            )
            for task in plan.tasks:
                task_db_id = f"task_{uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO tasks (
                        id, plan_id, task_id, title, agent, task_type, description,
                        status, acceptance_criteria_json, dependencies_json, risks_json,
                        goal, boundary, input_materials_json, tool_permissions_json,
                        deliverable_format, evidence_requirements_json,
                        blocking_conditions_json, decision_owner, next_action,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_db_id,
                        plan_id,
                        task.task_id,
                        task.title,
                        task.agent,
                        task.task_type,
                        task.description,
                        "pending",
                        _json(task.acceptance_criteria),
                        _json(task.dependencies),
                        _json(task.risks),
                        task.goal,
                        task.boundary,
                        _json(task.input_materials),
                        _json(task.tool_permissions),
                        task.deliverable_format,
                        _json(task.evidence_requirements),
                        _json(task.blocking_conditions),
                        task.decision_owner,
                        task.next_action,
                        now,
                        now,
                    ),
                )
                self._insert_event(conn, task_db_id, "created", "Task package created from planner output", asdict(task))
        return plan_id

    def list_tasks(self, plan_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM tasks"
        clauses: list[str] = []
        params: list[Any] = []
        if plan_id:
            clauses.append("plan_id = ?")
            params.append(plan_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at ASC, task_id ASC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_task_dict(row) for row in rows]

    def update_status(self, task_db_id: str, status: str, message: str = "") -> None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid task status: {status}")
        now = _now()
        with self._connect() as conn:
            result = conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, task_db_id),
            )
            if result.rowcount == 0:
                raise ValueError(f"Task not found: {task_db_id}")
            self._insert_event(
                conn,
                task_db_id,
                "status_changed",
                message or f"Status changed to {status}",
                {"status": status},
            )

    def update_next_action(self, task_db_id: str, next_action: str) -> None:
        now = _now()
        with self._connect() as conn:
            result = conn.execute(
                "UPDATE tasks SET next_action = ?, updated_at = ? WHERE id = ?",
                (next_action, now, task_db_id),
            )
            if result.rowcount == 0:
                raise ValueError(f"Task not found: {task_db_id}")
            self._insert_event(conn, task_db_id, "next_action_updated", next_action, {"next_action": next_action})

    def add_evidence_package(self, evidence: EvidencePackage) -> str:
        evidence_id = f"evidence_{uuid4().hex[:12]}"
        with self._connect() as conn:
            self._ensure_task_exists(conn, evidence.task_db_id)
            conn.execute(
                """
                INSERT INTO evidence_packages (
                    id, task_db_id, agent_name, completed_work, evidence_locations_json,
                    commands_run_json, changed_files_json, risks_json,
                    suggested_next_steps_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    evidence.task_db_id,
                    evidence.agent_name,
                    evidence.completed_work,
                    _json(evidence.evidence_locations),
                    _json(evidence.commands_run),
                    _json(evidence.changed_files),
                    _json(evidence.risks),
                    _json(evidence.suggested_next_steps),
                    _now(),
                ),
            )
            self._insert_event(
                conn,
                evidence.task_db_id,
                "evidence_submitted",
                f"Evidence package submitted by {evidence.agent_name}",
                {"evidence_id": evidence_id, **asdict(evidence)},
            )
        return evidence_id

    def list_evidence(self, task_db_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM evidence_packages"
        params: list[Any] = []
        if task_db_id:
            query += " WHERE task_db_id = ?"
            params.append(task_db_id)
        query += " ORDER BY created_at ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_evidence_dict(row) for row in rows]

    def add_review(self, review: ReviewRecord) -> str:
        review_id = f"review_{uuid4().hex[:12]}"
        with self._connect() as conn:
            self._ensure_task_exists(conn, review.task_db_id)
            conn.execute(
                """
                INSERT INTO reviews (
                    id, task_db_id, reviewer_agent, passed, issues_json,
                    summary, evidence_package_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    review.task_db_id,
                    review.reviewer_agent,
                    1 if review.passed else 0,
                    _json(review.issues),
                    review.summary,
                    review.evidence_package_id,
                    _now(),
                ),
            )
            self._insert_event(
                conn,
                review.task_db_id,
                "review_submitted",
                review.summary,
                {"review_id": review_id, **asdict(review)},
            )
        return review_id

    def create_conflict(self, conflict: ConflictRecord) -> str:
        if conflict.status not in VALID_CONFLICT_STATUSES:
            raise ValueError(f"Invalid conflict status: {conflict.status}")
        conflict_id = f"conflict_{uuid4().hex[:12]}"
        now = _now()
        with self._connect() as conn:
            self._ensure_task_exists(conn, conflict.task_db_id)
            conn.execute(
                """
                INSERT INTO conflicts (
                    id, task_db_id, conflict_type, agents_involved_json, claims_json,
                    evidence_refs_json, decision_owner, status, final_decision,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conflict_id,
                    conflict.task_db_id,
                    conflict.conflict_type,
                    _json(conflict.agents_involved),
                    _json(conflict.claims),
                    _json(conflict.evidence_refs),
                    conflict.decision_owner,
                    conflict.status,
                    conflict.final_decision,
                    now,
                    now,
                ),
            )
            self._insert_event(
                conn,
                conflict.task_db_id,
                "conflict_created",
                f"Conflict created: {conflict.conflict_type}",
                {"conflict_id": conflict_id, **asdict(conflict)},
            )
        return conflict_id

    def record_decision(self, decision: DecisionRecord) -> str:
        decision_id = f"decision_{uuid4().hex[:12]}"
        now = _now()
        with self._connect() as conn:
            conflict = conn.execute("SELECT * FROM conflicts WHERE id = ?", (decision.conflict_id,)).fetchone()
            if not conflict:
                raise ValueError(f"Conflict not found: {decision.conflict_id}")
            conn.execute(
                """
                INSERT INTO decisions (
                    id, conflict_id, decision_owner, decision, rationale,
                    evidence_refs_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision_id,
                    decision.conflict_id,
                    decision.decision_owner,
                    decision.decision,
                    decision.rationale,
                    _json(decision.evidence_refs),
                    now,
                ),
            )
            conn.execute(
                "UPDATE conflicts SET status = ?, final_decision = ?, updated_at = ? WHERE id = ?",
                ("resolved", decision.decision, now, decision.conflict_id),
            )
            self._insert_event(
                conn,
                conflict["task_db_id"],
                "decision_recorded",
                decision.decision,
                {"decision_id": decision_id, **asdict(decision)},
            )
        return decision_id

    def get_ready_tasks(self, plan_id: str) -> list[dict[str, Any]]:
        """Return pending tasks whose dependencies are already done."""
        tasks = self.list_tasks(plan_id=plan_id)
        done_task_ids = {task["task_id"] for task in tasks if task["status"] == "done"}
        ready: list[dict[str, Any]] = []
        for task in tasks:
            if task["status"] != "pending":
                continue
            dependencies = task["dependencies"]
            if all(dep in done_task_ids for dep in dependencies):
                ready.append(task)
        return ready

    def _ensure_task_exists(self, conn: sqlite3.Connection, task_db_id: str) -> None:
        row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_db_id,)).fetchone()
        if not row:
            raise ValueError(f"Task not found: {task_db_id}")

    def _insert_event(
        self,
        conn: sqlite3.Connection,
        task_db_id: str,
        event_type: str,
        message: str,
        payload: dict[str, Any],
    ) -> None:
        conn.execute(
            """
            INSERT INTO task_events (id, task_db_id, event_type, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (f"event_{uuid4().hex[:12]}", task_db_id, event_type, message, _json(payload), _now()),
        )

    def _row_to_task_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "plan_id": row["plan_id"],
            "task_id": row["task_id"],
            "title": row["title"],
            "agent": row["agent"],
            "task_type": row["task_type"],
            "description": row["description"],
            "status": row["status"],
            "acceptance_criteria": _loads(row["acceptance_criteria_json"]),
            "dependencies": _loads(row["dependencies_json"]),
            "risks": _loads(row["risks_json"]),
            "goal": row["goal"],
            "boundary": row["boundary"],
            "input_materials": _loads(row["input_materials_json"]),
            "tool_permissions": _loads(row["tool_permissions_json"]),
            "deliverable_format": row["deliverable_format"],
            "evidence_requirements": _loads(row["evidence_requirements_json"]),
            "blocking_conditions": _loads(row["blocking_conditions_json"]),
            "decision_owner": row["decision_owner"],
            "next_action": row["next_action"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _row_to_evidence_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "task_db_id": row["task_db_id"],
            "agent_name": row["agent_name"],
            "completed_work": row["completed_work"],
            "evidence_locations": _loads(row["evidence_locations_json"]),
            "commands_run": _loads(row["commands_run_json"]),
            "changed_files": _loads(row["changed_files_json"]),
            "risks": _loads(row["risks_json"]),
            "suggested_next_steps": _loads(row["suggested_next_steps_json"]),
            "created_at": row["created_at"],
        }


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _loads(value: str) -> Any:
    if not value:
        return []
    return json.loads(value)

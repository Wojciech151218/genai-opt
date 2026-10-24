from __future__ import annotations

import json
import re
import sqlite3
import threading
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from genai_opt.env import find_project_root
from genai_opt.optimizer_engine.checkpointer.sqlite_checkpointer import SqliteCheckpointer

DEFAULT_DASHBOARD_API_HOST = "localhost"
DEFAULT_DASHBOARD_API_PORT = 8766

_CHECKPOINT_DETAIL_RE = re.compile(r"^/api/checkpoints/(\d+)$")


def discover_databases(checkpoints_dir: Path, project_root: Path | None = None) -> list[dict[str, Any]]:
    """Find SQLite database files inside the checkpoints directory."""
    if not checkpoints_dir.is_dir():
        return []

    root = (project_root or find_project_root()).resolve()
    candidates: list[Path] = []
    for pattern in ("*.db", "*.sqlite", "*.sqlite3"):
        candidates.extend(checkpoints_dir.rglob(pattern))

    unique_files = {path.resolve() for path in candidates if path.is_file()}
    sorted_files = sorted(unique_files, key=lambda p: p.stat().st_mtime, reverse=True)

    results: list[dict[str, Any]] = []
    for file_path in sorted_files:
        stat = file_path.stat()
        try:
            display_path = str(file_path.relative_to(root))
        except ValueError:
            display_path = str(file_path)

        try:
            name = str(file_path.relative_to(checkpoints_dir.resolve()))
        except ValueError:
            name = file_path.name

        results.append(
            {
                "name": name,
                "path": display_path,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
            }
        )
    return results


def resolve_database_path(db_param: str, checkpoints_dir: Path, project_root: Path | None = None) -> Path:
    """Resolve a requested database path without creating missing files."""
    cleaned = db_param.strip()
    if not cleaned:
        raise ValueError("Missing 'db' query parameter.")

    root = (project_root or find_project_root()).resolve()
    raw_path = Path(cleaned)

    search_candidates = (
        [raw_path]
        if raw_path.is_absolute()
        else [
            checkpoints_dir / raw_path,
            root / raw_path,
        ]
    )

    for candidate in search_candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved

    raise FileNotFoundError(f"Database file not found: {cleaned}")


class DashboardAPIServer:
    """Lightweight read-only HTTP server exposing SQLite checkpoint history to the UI."""

    def __init__(
        self,
        host: str = DEFAULT_DASHBOARD_API_HOST,
        port: int = DEFAULT_DASHBOARD_API_PORT,
        *,
        checkpoints_dir: Path | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.project_root = find_project_root().resolve()
        self.checkpoints_dir = (checkpoints_dir or (self.project_root / ".checkpoints")).resolve()
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def bound_port(self) -> int:
        if self._httpd is not None:
            return int(self._httpd.server_address[1])
        return self.port

    def start(self) -> bool:
        """Start serving HTTP requests in a daemon thread. Returns False if port is busy."""
        outer = self

        class RequestHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()
                self.wfile.write(body)

            def do_OPTIONS(self) -> None:
                self.send_response(HTTPStatus.NO_CONTENT)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                route = parsed.path.rstrip("/") or "/"
                query = parse_qs(parsed.query)

                try:
                    if route == "/api/health":
                        self._send_json({"status": "ok"})
                        return

                    if route == "/api/databases":
                        dbs = discover_databases(outer.checkpoints_dir, project_root=outer.project_root)
                        self._send_json({"databases": dbs})
                        return

                    if route == "/api/experiments":
                        db_param = query.get("db", [""])[0]
                        db_file = resolve_database_path(
                            db_param, outer.checkpoints_dir, project_root=outer.project_root
                        )
                        reader: SqliteCheckpointer[Any, Any] = SqliteCheckpointer(db_path=db_file)
                        experiments = [rec.model_dump() for rec in reader.list_experiments()]
                        self._send_json({"db": db_param, "experiments": experiments})
                        return

                    if route == "/api/checkpoints":
                        db_param = query.get("db", [""])[0]
                        experiment_id = query.get("experiment_id", [""])[0].strip()
                        if not experiment_id:
                            raise ValueError("Missing 'experiment_id' query parameter.")
                        db_file = resolve_database_path(
                            db_param, outer.checkpoints_dir, project_root=outer.project_root
                        )
                        reader = SqliteCheckpointer(db_path=db_file, experiment_id=experiment_id)
                        checkpoints = [rec.model_dump() for rec in reader.list_checkpoints(experiment_id)]
                        self._send_json(
                            {
                                "db": db_param,
                                "experiment_id": experiment_id,
                                "checkpoints": checkpoints,
                            }
                        )
                        return

                    detail_match = _CHECKPOINT_DETAIL_RE.match(route)
                    if detail_match:
                        checkpoint_id = int(detail_match.group(1))
                        db_param = query.get("db", [""])[0]
                        db_file = resolve_database_path(
                            db_param, outer.checkpoints_dir, project_root=outer.project_root
                        )
                        reader = SqliteCheckpointer(db_path=db_file)
                        detail = reader.get_checkpoint(checkpoint_id)
                        if detail is None:
                            self._send_json(
                                {"error": f"Checkpoint {checkpoint_id} not found."},
                                status=HTTPStatus.NOT_FOUND,
                            )
                            return
                        self._send_json(detail.model_dump(by_alias=True))
                        return

                    self._send_json({"error": f"Unknown endpoint: {route}"}, status=HTTPStatus.NOT_FOUND)

                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                except FileNotFoundError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                except sqlite3.DatabaseError as exc:
                    self._send_json({"error": f"SQLite error: {exc}"}, status=HTTPStatus.BAD_REQUEST)

        class ReusableThreadingHTTPServer(ThreadingHTTPServer):
            allow_reuse_address = True

        try:
            self._httpd = ReusableThreadingHTTPServer((self.host, self.port), RequestHandler)
        except OSError:
            self._httpd = None
            return False

        self._thread = threading.Thread(target=self._httpd.serve_forever, name="dashboard-db-api", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        """Stop the background HTTP server."""
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

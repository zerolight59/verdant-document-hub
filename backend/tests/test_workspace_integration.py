"""Integration checks against a disposable PostgreSQL database, never SQLite or app data.

Run with TEST_POSTGRES_ADMIN_URL set to a PostgreSQL account allowed to create databases.
Only the randomly named verdant_test_* database created by this fixture is removed.
"""

import os
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models import Employee


@pytest.fixture(scope="module")
def test_engine():
    admin_url = os.getenv("TEST_POSTGRES_ADMIN_URL")
    if not admin_url:
        pytest.skip("Set TEST_POSTGRES_ADMIN_URL to run isolated PostgreSQL integration tests")
    url = make_url(admin_url)
    assert url.get_backend_name() == "postgresql"
    name = "verdant_test_" + uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
    engine = create_engine(url.set(database=name))
    original = {
        key: getattr(settings, key)
        for key in (
            "verdant_db_host",
            "verdant_db_port",
            "verdant_db_user",
            "verdant_db_password",
            "verdant_db_name",
        )
    }
    try:
        settings.verdant_db_host = url.host or "localhost"
        settings.verdant_db_port = url.port or 5432
        settings.verdant_db_user = url.username or "postgres"
        settings.verdant_db_password = url.password or ""
        settings.verdant_db_name = name
        command.upgrade(Config("alembic.ini"), "head")
        yield engine
    finally:
        for key, value in original.items():
            setattr(settings, key, value)
        engine.dispose()
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        admin.dispose()


@pytest.fixture
def env(test_engine, tmp_path, monkeypatch):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    monkeypatch.setattr(settings, "storage_root", tmp_path)
    employees = {}
    encoded = hash_password("test-password")
    for code in ("owner", "writer", "reviewer", "editor", "outsider", "admin"):
        employee = Employee(
            employee_code=code,
            username=code,
            name=code.title(),
            email=code + "@example.test",
            password_hash=encoded,
            is_admin=code in {"owner", "admin"},
        )
        session.add(employee)
        session.flush()
        employees[code] = employee.id
    session.commit()

    def database():
        yield session

    app.dependency_overrides[get_db] = database
    client = TestClient(app, headers={"origin": settings.frontend_origin})

    def login(code):
        response = client.post(
            "/api/auth/login", json={"employee_code": code, "password": "test-password"}
        )
        assert response.status_code == 200, response.text
        return response

    login("owner")
    project = client.post("/api/projects", json={"name": "Integration project"}).json()
    project_id = project["id"]
    for code in ("writer", "reviewer", "editor"):
        assert (
            client.post(
                f"/api/projects/{project_id}/members",
                json={"employee_id": employees[code], "access_level": "EDIT"},
            ).status_code
            == 201
        )
    stage = client.post(
        f"/api/projects/{project_id}/stages", json={"name": "Design", "position": 1}
    ).json()
    requirement = client.post(
        f"/api/projects/{project_id}/requirements",
        json={
            "title": "Technical drawing",
            "document_type_name": "Drawing",
            "stage_id": stage["id"],
            "responsible_employee_id": employees["writer"],
            "reviewer_employee_id": employees["reviewer"],
        },
    ).json()
    yield client, login, employees, project_id, requirement["id"], session
    client.close()
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()


def upload(client, requirement_id, name="drawing.pdf"):
    return client.post(
        f"/api/documents/requirements/{requirement_id}/versions",
        files={"file": (name, b"%PDF-1.4 test file", "application/pdf")},
        data={"change_summary": "Updated dimensions"},
    )


def test_cookie_login_and_csrf(env):
    client, login, _, _, _, _ = env
    response = login("writer")
    assert "access_token" not in response.json()
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert client.get("/api/auth/me").status_code == 200
    assert (
        client.post(
            "/api/projects",
            json={"name": "Attacker"},
            headers={"origin": "https://attacker.example"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"employee_code": "writer", "password": "test-password"},
            headers={"origin": "https://attacker.example"},
        ).status_code
        == 403
    )
    assert client.get("/api/auth/employees").json()[0].keys() == {
        "id",
        "employee_code",
        "name",
        "job_title",
    }
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_strict_assignment_and_review_lifecycle(env):
    client, login, employees, project_id, requirement_id, _ = env
    for code in ("owner", "reviewer", "editor", "outsider", "admin"):
        login(code)
        assert upload(client, requirement_id).status_code == 403, code
    login("writer")
    version = upload(client, requirement_id).json()["id"]
    for code in ("owner", "reviewer", "editor", "admin"):
        login(code)
        assert client.post(f"/api/documents/versions/{version}/submit").status_code == 403
    login("writer")
    assert client.post(f"/api/documents/versions/{version}/submit").status_code == 200
    assert upload(client, requirement_id).status_code == 409
    login("owner")
    assert (
        client.patch(
            f"/api/projects/requirements/{requirement_id}/assign",
            json={
                "responsible_employee_id": employees["editor"],
                "reviewer_employee_id": employees["reviewer"],
            },
        ).status_code
        == 409
    )
    dashboard = client.get(f"/api/projects/{project_id}/dashboard").json()
    review = dashboard["requirements"][0]["current_version"]["review"]["id"]
    for code in ("owner", "writer", "editor", "outsider", "admin"):
        login(code)
        assert client.post(f"/api/documents/reviews/{review}/start").status_code == 403
        assert (
            client.post(
                f"/api/documents/reviews/{review}/decision", json={"decision": "APPROVED"}
            ).status_code
            == 403
        )
    login("reviewer")
    assert (
        client.post(
            f"/api/documents/reviews/{review}/decision", json={"decision": "APPROVED"}
        ).status_code
        == 409
    )
    assert client.post(f"/api/documents/reviews/{review}/start").status_code == 200
    assert (
        client.post(
            f"/api/documents/reviews/{review}/decision",
            json={"decision": "CHANGES_REQUESTED", "comment": " "},
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/documents/reviews/{review}/decision",
            json={"decision": "CHANGES_REQUESTED", "comment": "Fix the diameter"},
        ).status_code
        == 200
    )
    login("writer")
    assert client.post(f"/api/documents/versions/{version}/submit").status_code == 409
    newer = upload(client, requirement_id).json()["id"]
    assert client.post(f"/api/documents/versions/{newer}/submit").status_code == 200
    login("reviewer")
    assert client.post(f"/api/documents/reviews/{review}/start").status_code == 409
    dashboard = client.get(f"/api/projects/{project_id}/dashboard").json()
    new_review = dashboard["requirements"][0]["current_version"]["review"]["id"]
    assert client.post(f"/api/documents/reviews/{new_review}/start").status_code == 200
    assert (
        client.post(
            f"/api/documents/reviews/{new_review}/decision",
            json={"decision": "APPROVED", "comment": "Dimensions confirmed"},
        ).status_code
        == 200
    )


def test_private_projects_and_document_sharing(env):
    client, login, employees, project_id, requirement_id, _ = env
    login("writer")
    version_id = upload(client, requirement_id).json()["id"]
    for code in ("admin", "outsider"):
        login(code)
        assert client.get("/api/projects").json() == []
        assert client.get(f"/api/projects/{project_id}/dashboard").status_code == 403
        assert client.get(f"/api/documents/files/project/{version_id}").status_code == 403
        assert client.get("/api/search?q=drawing").json() == []
    login("owner")
    assert (
        client.put(
            f"/api/projects/requirements/{requirement_id}/permissions",
            json={"employee_id": employees["outsider"], "access_level": "EDIT"},
        ).status_code
        == 200
    )
    login("outsider")
    assert client.get(f"/api/documents/files/project/{version_id}").status_code == 200
    assert upload(client, requirement_id).status_code == 403
    assert client.get(f"/api/projects/{project_id}/dashboard").status_code == 403
    login("owner")
    assert client.delete(f"/api/documents/requirements/{requirement_id}").status_code == 200
    login("outsider")
    assert client.get(f"/api/documents/files/project/{version_id}").status_code == 404


def test_research_navigation_links_and_preview(env):
    client, login, _, project_id, _, _ = env
    category = client.post("/api/research/categories", json={"name": "Metals"}).json()
    child = client.post(
        "/api/research/categories", json={"name": "Steel", "parent_id": category["id"]}
    ).json()

    def research(name):
        response = client.post(
            "/api/research",
            data={"category_id": child["id"], "name": name},
            files={"file": ("notes.txt", b"Research content", "text/html")},
        )
        assert response.status_code == 201, response.text
        return response.json()

    first, second = research("First study"), research("Related study")
    assert (
        client.post(
            f"/api/research/{first['id']}/links", json={"project_id": project_id}
        ).status_code
        == 200
    )
    assert client.post(f"/api/research/{first['id']}/related/{second['id']}").status_code == 200
    assert client.post(f"/api/research/{first['id']}/related/{first['id']}").status_code == 422
    data = next(d for d in client.get("/api/research").json() if d["id"] == first["id"])
    assert data["projects"][0]["id"] == project_id
    assert data["related"][0]["id"] == second["id"]
    version = data["current_version"]
    assert version["mime_type"] == "text/plain"
    assert (
        client.get(f"/api/viewer/research/{version['id']}").json()["sections"][0]["text"]
        == "Research content"
    )
    login("outsider")
    data = next(d for d in client.get("/api/research").json() if d["id"] == first["id"])
    assert data["projects"] == []  # Private project names do not leak into the open wiki.
    assert client.delete(f"/api/research/{first['id']}/links/{project_id}").status_code == 403
    login("owner")
    assert client.delete(f"/api/research/{first['id']}/related/{second['id']}").status_code == 200
    assert client.delete(f"/api/research/{first['id']}/links/{project_id}").status_code == 200
    assert client.delete(f"/api/research/{first['id']}").status_code == 200
    assert client.get(f"/api/research/files/{version['id']}").status_code == 404
    assert client.get(f"/api/viewer/research/{version['id']}").status_code == 404


def test_unsafe_formats_rejected(env):
    client, login, _, _, requirement_id, _ = env
    login("writer")
    assert upload(client, requirement_id, "malicious.html").status_code == 415
    assert upload(client, requirement_id, "image.svg").status_code == 415


def test_showcase_is_additive_and_repeatable(test_engine, tmp_path, monkeypatch):
    from sqlalchemy import func, select
    from sqlalchemy.orm import sessionmaker

    from app.models import DocumentRequirement, DocumentVersion, Project, ResearchDocument
    from scripts import seed_demo
    from scripts.seed_showcase import seed_showcase

    connection = test_engine.connect()
    transaction = connection.begin()
    factory = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    monkeypatch.setattr(seed_demo, "SessionLocal", factory)
    monkeypatch.setattr(settings, "storage_root", tmp_path)
    try:
        seed_demo.seed()
        with factory() as db:
            original = db.scalar(select(DocumentVersion)).checksum_sha256
            result = seed_showcase(db, tmp_path)
            assert result == {
                "created": True,
                "projects": 3,
                "requirements": 14,
                "project_versions": 13,
                "research_documents": 8,
                "new_employees": 2,
                "categories": 8,
            }
            count = db.scalar(select(func.count()).select_from(Project))
            assert count == 4
            assert db.scalar(select(func.count()).select_from(ResearchDocument)) == 9
            draft = db.scalar(
                select(DocumentRequirement).where(
                    DocumentRequirement.title == "Design risk assessment"
                )
            )
            draft.description = "Edited during a demonstration"
            db.commit()
            assert seed_showcase(db, tmp_path)["created"] is False
            db.refresh(draft)
            assert draft.description == "Edited during a demonstration"
            assert db.scalar(select(func.count()).select_from(Project)) == count
            assert (
                db.scalar(select(DocumentVersion).order_by(DocumentVersion.id)).checksum_sha256
                == original
            )
    finally:
        transaction.rollback()
        connection.close()


def test_showcase_rejects_non_demo_identities(env, tmp_path):
    from scripts.seed_showcase import seed_showcase

    db = env[-1]
    with pytest.raises(ValueError, match="original active demo identities"):
        seed_showcase(db, tmp_path)
    assert not list(tmp_path.rglob("*.pdf"))


def test_browser_workflows(test_engine, tmp_path):
    """Optional browser workflow against the disposable database and isolated file storage."""
    if os.getenv("TEST_RUN_BROWSER") != "1":
        pytest.skip(
            "Set TEST_RUN_BROWSER=1, start frontend on localhost:3000, and install Playwright"
        )
    import shutil
    import socket
    import subprocess
    import sys
    import time
    from pathlib import Path
    from urllib.error import URLError
    from urllib.request import urlopen

    root = Path(__file__).resolve().parents[2]
    url = test_engine.url
    environment = dict(os.environ)
    environment.update(
        {
            "VERDANT_DB_HOST": url.host or "localhost",
            "VERDANT_DB_PORT": str(url.port or 5432),
            "VERDANT_DB_USER": url.username or "postgres",
            "VERDANT_DB_PASSWORD": url.password or "",
            "VERDANT_DB_NAME": url.database,
            "STORAGE_ROOT": str(tmp_path),
            "FRONTEND_ORIGIN": "http://localhost:3000",
            "ENVIRONMENT": "development",
        }
    )
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    subprocess.run(
        [sys.executable, "-m", "scripts.seed_demo"],
        cwd=root / "backend",
        env=environment,
        check=True,
        creationflags=flags,
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    environment["VERDANT_TEST_API_ORIGIN"] = f"http://localhost:{port}"
    with (tmp_path / "api.log").open("w") as log:
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=root / "backend",
            env=environment,
            stdout=log,
            stderr=log,
            creationflags=flags,
        )
        try:
            ready = False
            for _ in range(150):
                if server.poll() is not None:
                    break
                try:
                    with urlopen(f"http://localhost:{port}/api/health", timeout=1) as response:
                        ready = response.status == 200
                    if ready:
                        break
                except (URLError, TimeoutError):
                    time.sleep(0.1)
            assert ready, "Isolated API did not start"
            result = subprocess.run(
                [
                    shutil.which("node"),
                    "tests/capture-guide.mjs"
                    if os.getenv("TEST_CAPTURE_GUIDE") == "1"
                    else "tests/workspace.e2e.mjs",
                ],
                cwd=root / "frontend",
                env=environment,
                capture_output=True,
                text=True,
                timeout=240,
                creationflags=flags,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            print(result.stdout)
        finally:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill.exe", "/PID", str(server.pid), "/T", "/F"],
                    check=False,
                    capture_output=True,
                    creationflags=flags,
                )
            else:
                server.terminate()
            server.wait(timeout=15)

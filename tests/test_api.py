"""End-to-end API tests: python -m pytest tests/test_api.py"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.python import create_app  # noqa: E402
from setup_db import setup, DEMO_STAFF  # noqa: E402

PASSWORDS = {u: p for u, _, _, p in DEMO_STAFF}
HDR = {"X-Pulse-Client": "dashboard"}


@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
    })
    setup(app)
    return app


class Session:
    def __init__(self, app, username):
        self.c = app.test_client()
        r = self.c.post("/api/auth/login", headers=HDR,
                        json={"username": username, "password": PASSWORDS[username]})
        assert r.status_code == 200, r.get_json()
        self.csrf = r.get_json()["csrfToken"]

    def get(self, url):
        return self.c.get(url)

    def post(self, url, json=None):
        return self.c.post(url, json=json or {}, headers={"X-CSRF-Token": self.csrf})

    def patch(self, url, json):
        return self.c.patch(url, json=json, headers={"X-CSRF-Token": self.csrf})


def register(s, symptoms="headache", severity=3, age=30, **extra):
    clinical = {"symptoms": symptoms, "age": age, "warnings": [],
                "warningsReviewed": True, "vitals": {}}
    clinical.update(extra)
    a = s.post("/api/assessments", clinical)
    assert a.status_code == 200, a.get_json()
    body = dict(clinical, name="Test Patient", gender="Female", disease="",
                severity=severity, review=True, overrideReason="",
                draftId=a.get_json()["draftId"])
    return s.post("/api/patients", body)


def test_health_and_static_frontend(app):
    c = app.test_client()
    assert c.get("/api/health").get_json()["status"] == "ok"
    assert b"Medicare" in c.get("/").data
    assert c.get("/app.js").status_code == 200
    assert c.get("/assessment.js").status_code == 200
    assert c.get("/style.css").status_code == 200
    assert c.get("/models.py").status_code == 404


def test_login_requirements(app):
    c = app.test_client()
    assert c.post("/api/auth/login", json={"username": "nurse", "password": "x"}).status_code == 403
    r = c.post("/api/auth/login", headers=HDR, json={"username": "nurse", "password": "wrong"})
    assert r.status_code == 401
    assert c.get("/api/dashboard").status_code == 401


def test_register_assign_discharge_flow(app):
    s = Session(app, "nurse")
    r = register(s)
    assert r.status_code == 201
    pid = r.get_json()["id"]
    assert r.get_json()["severityReview"]["reviewer"] == "Nurse Demo"  # from login, not client

    dash = s.get("/api/dashboard").get_json()
    assert len(dash["doctors"]) == 4 and len(dash["beds"]) == 8
    assert dash["patients"][0]["status"] == "waiting"

    a = s.post("/api/queue/assign-next")
    assert a.status_code == 200 and a.get_json()["status"] == "treatment"
    assert s.post("/api/queue/assign-next").status_code == 409  # nobody waiting

    d = s.post(f"/api/patients/{pid}/discharge")
    assert d.get_json()["status"] == "completed"
    assert s.post(f"/api/patients/{pid}/discharge").status_code == 409


def test_queue_orders_by_severity_then_arrival(app):
    s = Session(app, "doctor")
    register(s, "headache")                                 # medium
    r = register(s, "chest pain", severity=1)               # critical
    assert r.status_code == 201
    assigned = s.post("/api/queue/assign-next").get_json()
    assert assigned["severity"] == 1


def test_emergency_cannot_be_downgraded(app):
    s = Session(app, "nurse")
    r = register(s, "chest pain", severity=3)
    assert r.status_code == 400 and "downgraded" in r.get_json()["error"]


def test_override_requires_reason(app):
    s = Session(app, "nurse")
    r = register(s, "headache", severity=4)  # suggestion is 3
    assert r.status_code == 400 and "override" in r.get_json()["error"].lower()


def test_roles_enforced(app):
    rec = Session(app, "reception")
    assert rec.post("/api/queue/assign-next").status_code == 403
    assert rec.post("/api/assessments", {"symptoms": "x", "age": 30}).status_code == 403
    assert rec.post("/api/patients", {}).status_code == 403
    nurse = Session(app, "nurse")
    assert nurse.get("/api/audit").status_code == 403
    assert nurse.post("/api/resources/beds").status_code == 403


def test_csrf_required(app):
    s = Session(app, "nurse")
    r = s.c.post("/api/queue/assign-next", json={})
    assert r.status_code == 403


def test_admin_resources_and_audit(app):
    adm = Session(app, "admin")
    assert adm.post("/api/resources/doctors", {"name": "Dr. New"}).status_code == 201
    assert adm.post("/api/resources/beds").status_code == 201
    assert len(adm.get("/api/dashboard").get_json()["doctors"]) == 5
    assert adm.patch("/api/resources/beds/1", {"active": False}).status_code == 200
    assert len(adm.get("/api/staff").get_json()["items"]) == 4
    actions = [i["action"] for i in adm.get("/api/audit").get_json()["items"]]
    assert "login" in actions and "resource_add" in actions


def test_logout_invalidates_session(app):
    s = Session(app, "nurse")
    assert s.post("/api/auth/logout").status_code == 200
    assert s.get("/api/dashboard").status_code == 401

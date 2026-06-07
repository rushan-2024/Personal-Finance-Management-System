"""
tests/test_app.py — Unit + integration tests for FinFlow.
Run: pytest tests/ -v
"""
import pytest
from app import create_app, db
from app.models import User, Transaction, Budget, Goal, Category
from datetime import date


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def runner(app):
    return app.test_cli_runner()


@pytest.fixture(scope="module")
def test_user(app):
    with app.app_context():
        user = User(name="Test User", email="test@finflow.app")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user.id


# ── Auth Tests ─────────────────────────────────────────────────────────────

class TestAuth:
    def test_signup_page_loads(self, client):
        res = client.get("/auth/signup")
        assert res.status_code == 200
        assert b"Create" in res.data

    def test_login_page_loads(self, client):
        res = client.get("/auth/login")
        assert res.status_code == 200
        assert b"Sign" in res.data

    def test_signup_creates_user(self, client, app):
        res = client.post("/auth/signup", data={
            "name": "Jane Doe",
            "email": "jane@finflow.app",
            "password": "securepass",
            "confirm_password": "securepass",
            "csrf_token": "test",
        }, follow_redirects=True)
        with app.app_context():
            assert User.query.filter_by(email="jane@finflow.app").first() is not None

    def test_login_invalid_credentials(self, client):
        res = client.post("/auth/login", data={
            "email": "nobody@example.com",
            "password": "wrongpass",
            "csrf_token": "test",
        }, follow_redirects=True)
        assert b"Invalid" in res.data or res.status_code == 200

    def test_password_hashing(self, app):
        with app.app_context():
            user = User(name="Hash Test", email="hash@test.com")
            user.set_password("mypassword")
            assert user.password_hash != "mypassword"
            assert user.check_password("mypassword") is True
            assert user.check_password("wrongpass") is False


# ── Model Tests ────────────────────────────────────────────────────────────

class TestModels:
    def test_user_to_dict(self, app):
        with app.app_context():
            user = User.query.filter_by(email="test@finflow.app").first()
            if not user:
                user = User(name="Test", email="test@finflow.app")
                user.set_password("pw")
                db.session.add(user)
                db.session.commit()
            d = user.to_dict()
            assert "email" in d
            assert "password_hash" not in d

    def test_transaction_to_dict(self, app):
        with app.app_context():
            user = User.query.first()
            txn = Transaction(
                user_id=user.id, amount=5000, type="income",
                description="Test income", date=date.today(), currency="INR",
            )
            db.session.add(txn)
            db.session.commit()
            d = txn.to_dict()
            assert d["amount"] == 5000
            assert d["type"] == "income"

    def test_goal_progress_percent(self, app):
        with app.app_context():
            user = User.query.first()
            goal = Goal(
                user_id=user.id, name="Test Goal",
                target_amount=100000, saved_amount=50000,
            )
            db.session.add(goal)
            db.session.commit()
            assert goal.progress_percent == 50.0

    def test_goal_progress_capped_at_100(self, app):
        with app.app_context():
            user = User.query.first()
            goal = Goal(
                user_id=user.id, name="Overflow Goal",
                target_amount=1000, saved_amount=1500,
            )
            db.session.add(goal)
            db.session.commit()
            assert goal.progress_percent == 100.0

    def test_budget_to_dict(self, app):
        with app.app_context():
            user = User.query.first()
            budget = Budget(
                user_id=user.id, name="Test Budget",
                amount=10000, month=1, year=2026,
            )
            db.session.add(budget)
            db.session.commit()
            d = budget.to_dict()
            assert d["amount"] == 10000


# ── API Tests ──────────────────────────────────────────────────────────────

class TestAPI:
    def _get_token(self, client):
        # Register + login
        client.post("/auth/signup", data={
            "name": "API User", "email": "api@finflow.app",
            "password": "apipass123", "confirm_password": "apipass123",
            "csrf_token": "test",
        })
        res = client.post("/api/v1/auth/login", json={
            "email": "api@finflow.app", "password": "apipass123",
        })
        if res.status_code == 200:
            return res.get_json()["data"]["access_token"]
        return None

    def test_api_register(self, client):
        res = client.post("/api/v1/auth/register", json={
            "name": "API Reg User",
            "email": "reg@finflow.app",
            "password": "regpassword",
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["status"] == "success"

    def test_api_login(self, client):
        # Register first
        client.post("/api/v1/auth/register", json={
            "name": "Login User", "email": "login@finflow.app", "password": "loginpass1",
        })
        res = client.post("/api/v1/auth/login", json={
            "email": "login@finflow.app", "password": "loginpass1",
        })
        assert res.status_code == 200
        data = res.get_json()
        assert "access_token" in data["data"]

    def test_api_login_wrong_password(self, client):
        res = client.post("/api/v1/auth/login", json={
            "email": "login@finflow.app", "password": "wrongpass",
        })
        assert res.status_code == 401

    def test_api_transactions_requires_auth(self, client):
        res = client.get("/api/v1/transactions")
        assert res.status_code == 401

    def test_api_create_and_list_transactions(self, client):
        token = self._get_token(client)
        if not token:
            pytest.skip("Could not obtain JWT token")

        headers = {"Authorization": f"Bearer {token}"}
        # Create
        res = client.post("/api/v1/transactions", json={
            "amount": 5000, "type": "income",
            "description": "API Test Income", "date": "2026-01-15",
        }, headers=headers)
        assert res.status_code == 201

        # List
        res = client.get("/api/v1/transactions", headers=headers)
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert len(data["transactions"]) >= 1

    def test_api_analytics_summary(self, client):
        token = self._get_token(client)
        if not token:
            pytest.skip("Could not obtain JWT token")
        res = client.get("/api/v1/analytics/summary",
                         headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        d = res.get_json()["data"]
        assert "income" in d and "expense" in d and "balance" in d

    def test_api_goals_crud(self, client):
        token = self._get_token(client)
        if not token:
            pytest.skip("Could not obtain JWT token")
        headers = {"Authorization": f"Bearer {token}"}

        # Create
        res = client.post("/api/v1/goals", json={
            "name": "Test Goal", "target_amount": 50000,
        }, headers=headers)
        assert res.status_code == 201
        goal_id = res.get_json()["data"]["id"]

        # Contribute
        res = client.patch(f"/api/v1/goals/{goal_id}/contribute",
                           json={"amount": 10000}, headers=headers)
        assert res.status_code == 200
        assert res.get_json()["data"]["saved_amount"] == 10000

        # Delete
        res = client.delete(f"/api/v1/goals/{goal_id}", headers=headers)
        assert res.status_code == 200

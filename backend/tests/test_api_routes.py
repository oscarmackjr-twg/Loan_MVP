"""Tests for API routes."""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.orm import Session

from api.main import app
from db.models import User, SalesTeam, PipelineRun, UserRole, RunStatus
from auth.security import create_access_token, get_password_hash
from db.connection import get_db


@pytest.fixture
def client(test_db_session, override_get_db):
    """Create test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers_admin(sample_admin_user):
    """Get auth headers for admin user."""
    token = create_access_token({"sub": str(sample_admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_sales(sample_sales_user):
    """Get auth headers for sales user."""
    token = create_access_token({"sub": str(sample_sales_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_success(self, client, sample_admin_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "admin",
                "password": "testpass"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "invalid",
                "password": "wrong"
            }
        )
        assert response.status_code == 401
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without auth."""
        response = client.get("/api/runs")
        assert response.status_code == 401


class TestRunsEndpoint:
    """Test runs endpoints."""
    
    def test_list_runs(self, client, auth_headers_admin, test_db_session):
        """Test listing runs."""
        # Create sample run
        run = PipelineRun(
            run_id="test_run_123",
            status=RunStatus.COMPLETED,
            total_loans=10,
            total_balance=100000.0
        )
        test_db_session.add(run)
        test_db_session.commit()
        
        response = client.get("/api/runs", headers=auth_headers_admin)
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) > 0
    
    def test_get_run(self, client, auth_headers_admin, test_db_session):
        """Test getting specific run."""
        run = PipelineRun(
            run_id="test_run_456",
            status=RunStatus.COMPLETED
        )
        test_db_session.add(run)
        test_db_session.commit()
        
        response = client.get(f"/api/runs/test_run_456", headers=auth_headers_admin)
        assert response.status_code == 200
        assert response.json()["run_id"] == "test_run_456"
    
    def test_sales_team_isolation(self, client, auth_headers_sales, test_db_session, sample_sales_team):
        """Test that sales team users only see their own runs."""
        # Create run for different sales team
        other_team = SalesTeam(name="Other Team")
        test_db_session.add(other_team)
        test_db_session.commit()
        
        other_run = PipelineRun(
            run_id="other_run",
            status=RunStatus.COMPLETED,
            sales_team_id=other_team.id
        )
        test_db_session.add(other_run)
        
        # Create run for user's sales team
        user_run = PipelineRun(
            run_id="user_run",
            status=RunStatus.COMPLETED,
            sales_team_id=sample_sales_team.id
        )
        test_db_session.add(user_run)
        test_db_session.commit()
        
        response = client.get("/api/runs", headers=auth_headers_sales)
        assert response.status_code == 200
        runs = response.json()
        
        # Should only see user's team run
        run_ids = [r["run_id"] for r in runs]
        assert "user_run" in run_ids
        assert "other_run" not in run_ids


class TestExceptionsEndpoint:
    """Test exceptions endpoints."""
    
    def test_get_exceptions(self, client, auth_headers_admin, test_db_session):
        """Test getting exceptions."""
        response = client.get("/api/exceptions", headers=auth_headers_admin)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_exceptions_with_filters(self, client, auth_headers_admin):
        """Test getting exceptions with filters."""
        response = client.get(
            "/api/exceptions",
            params={
                "exception_type": "purchase_price",
                "severity": "error"
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 200

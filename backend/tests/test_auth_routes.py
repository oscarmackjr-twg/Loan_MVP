"""Tests for authentication routes."""
import pytest
from fastapi.testclient import TestClient
from db.models import User, SalesTeam, UserRole
from auth.security import create_access_token


class TestUserRegistration:
    """Test user registration."""
    
    def test_register_user_admin(self, client, auth_headers_admin, test_db_session, sample_sales_team):
        """Test admin can register users."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@test.com",
                "username": "newuser",
                "password": "testpass",
                "full_name": "New User",
                "role": "analyst",
                "sales_team_id": None
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newuser@test.com"
    
    def test_register_sales_team_user(self, client, auth_headers_admin, test_db_session, sample_sales_team):
        """Test registering sales team user with sales_team_id."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "sales@test.com",
                "username": "salesuser",
                "password": "testpass",
                "full_name": "Sales User",
                "role": "sales_team",
                "sales_team_id": sample_sales_team.id
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["sales_team_id"] == sample_sales_team.id
    
    def test_register_sales_team_without_id(self, client, auth_headers_admin, test_db_session):
        """Test registering sales team user without sales_team_id fails."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "sales@test.com",
                "username": "salesuser",
                "password": "testpass",
                "full_name": "Sales User",
                "role": "sales_team",
                "sales_team_id": None
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 400
    
    def test_register_duplicate_email(self, client, auth_headers_admin, test_db_session, sample_admin_user):
        """Test registering with duplicate email fails."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": sample_admin_user.email,
                "username": "different",
                "password": "testpass",
                "full_name": "Different User",
                "role": "analyst"
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 400
    
    def test_register_non_admin_forbidden(self, client, auth_headers_sales):
        """Test non-admin cannot register users."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@test.com",
                "username": "test",
                "password": "testpass",
                "full_name": "Test User",
                "role": "analyst"
            },
            headers=auth_headers_sales
        )
        assert response.status_code == 403


class TestUserUpdate:
    """Test user update."""
    
    def test_update_user_admin(self, client, auth_headers_admin, test_db_session, sample_sales_team):
        """Test admin can update users."""
        # Create user to update
        user = User(
            email="update@test.com",
            username="update",
            hashed_password="hash",
            role=UserRole.ANALYST
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        response = client.put(
            f"/api/auth/users/{user.id}",
            json={
                "full_name": "Updated Name",
                "role": "sales_team",
                "sales_team_id": sample_sales_team.id
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"
        assert response.json()["role"] == "sales_team"
    
    def test_update_sales_team_assignment(self, client, auth_headers_admin, test_db_session, sample_sales_team):
        """Test updating sales team assignment."""
        user = User(
            email="update@test.com",
            username="update",
            hashed_password="hash",
            role=UserRole.ANALYST
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        response = client.put(
            f"/api/auth/users/{user.id}",
            json={
                "role": "sales_team",
                "sales_team_id": sample_sales_team.id
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        assert response.json()["sales_team_id"] == sample_sales_team.id
    
    def test_update_sales_team_without_id_fails(self, client, auth_headers_admin, test_db_session):
        """Test updating to sales_team without sales_team_id fails."""
        user = User(
            email="update@test.com",
            username="update",
            hashed_password="hash",
            role=UserRole.ANALYST
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        response = client.put(
            f"/api/auth/users/{user.id}",
            json={
                "role": "sales_team",
                "sales_team_id": None
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 400
    
    def test_update_own_role_forbidden(self, client, auth_headers_admin, test_db_session, sample_admin_user):
        """Test user cannot change own role."""
        response = client.put(
            f"/api/auth/users/{sample_admin_user.id}",
            json={
                "role": "sales_team"
            },
            headers=auth_headers_admin
        )
        assert response.status_code == 403


class TestUserList:
    """Test user listing."""
    
    def test_list_users_admin(self, client, auth_headers_admin, test_db_session):
        """Test admin can list users."""
        response = client.get("/api/auth/users", headers=auth_headers_admin)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_users_filter_by_role(self, client, auth_headers_admin, test_db_session):
        """Test filtering users by role."""
        response = client.get(
            "/api/auth/users",
            params={"role": "sales_team"},
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        users = response.json()
        assert all(u["role"] == "sales_team" for u in users)
    
    def test_list_users_non_admin_forbidden(self, client, auth_headers_sales):
        """Test non-admin cannot list users."""
        response = client.get("/api/auth/users", headers=auth_headers_sales)
        assert response.status_code == 403

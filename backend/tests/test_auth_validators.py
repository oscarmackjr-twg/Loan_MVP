"""Tests for authentication validators."""
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import User, SalesTeam, UserRole
from auth.validators import (
    validate_sales_team_assignment,
    validate_sales_team_access,
    validate_user_update,
    get_user_sales_team_id
)


class TestValidateSalesTeamAssignment:
    """Test sales team assignment validation."""
    
    def test_sales_team_with_assignment(self, test_db_session, sample_sales_team):
        """Test SALES_TEAM user with valid sales_team_id."""
        validate_sales_team_assignment(
            UserRole.SALES_TEAM,
            sample_sales_team.id,
            test_db_session
        )
        # Should not raise
    
    def test_sales_team_without_assignment(self, test_db_session):
        """Test SALES_TEAM user without sales_team_id."""
        with pytest.raises(HTTPException) as exc_info:
            validate_sales_team_assignment(
                UserRole.SALES_TEAM,
                None,
                test_db_session
            )
        assert exc_info.value.status_code == 400
    
    def test_sales_team_with_invalid_id(self, test_db_session):
        """Test SALES_TEAM user with invalid sales_team_id."""
        with pytest.raises(HTTPException) as exc_info:
            validate_sales_team_assignment(
                UserRole.SALES_TEAM,
                99999,  # Non-existent ID
                test_db_session
            )
        assert exc_info.value.status_code == 404
    
    def test_admin_without_assignment(self, test_db_session):
        """Test ADMIN user without sales_team_id (should be OK)."""
        validate_sales_team_assignment(
            UserRole.ADMIN,
            None,
            test_db_session
        )
        # Should not raise
    
    def test_analyst_without_assignment(self, test_db_session):
        """Test ANALYST user without sales_team_id (should be OK)."""
        validate_sales_team_assignment(
            UserRole.ANALYST,
            None,
            test_db_session
        )
        # Should not raise


class TestValidateSalesTeamAccess:
    """Test sales team access validation."""
    
    def test_admin_access_all(self, sample_admin_user):
        """Test admin can access all data."""
        validate_sales_team_access(sample_admin_user, None)
        validate_sales_team_access(sample_admin_user, 1)
        validate_sales_team_access(sample_admin_user, 999)
        # Should not raise
    
    def test_analyst_access_all(self, sample_admin_user):
        """Test analyst can access all data."""
        sample_admin_user.role = UserRole.ANALYST
        validate_sales_team_access(sample_admin_user, None)
        validate_sales_team_access(sample_admin_user, 1)
        # Should not raise
    
    def test_sales_team_access_own(self, sample_sales_user, sample_sales_team):
        """Test sales team user can access own team's data."""
        validate_sales_team_access(sample_sales_user, sample_sales_team.id)
        # Should not raise
    
    def test_sales_team_access_other(self, sample_sales_user):
        """Test sales team user cannot access other team's data."""
        with pytest.raises(HTTPException) as exc_info:
            validate_sales_team_access(sample_sales_user, 999)  # Different team
        assert exc_info.value.status_code == 403
    
    def test_sales_team_no_assignment(self, test_db_session):
        """Test sales team user without assignment."""
        user = User(
            email="test@test.com",
            username="test",
            hashed_password="hash",
            role=UserRole.SALES_TEAM,
            sales_team_id=None
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            validate_sales_team_access(user, None)
        assert exc_info.value.status_code == 403


class TestValidateUserUpdate:
    """Test user update validation."""
    
    def test_admin_can_update(self, test_db_session, sample_admin_user, sample_sales_team):
        """Test admin can update users."""
        target_user = User(
            email="target@test.com",
            username="target",
            hashed_password="hash",
            role=UserRole.ANALYST
        )
        test_db_session.add(target_user)
        test_db_session.commit()
        
        validate_user_update(
            target_user.id,
            UserRole.SALES_TEAM,
            sample_sales_team.id,
            sample_admin_user,
            test_db_session
        )
        # Should not raise
    
    def test_non_admin_cannot_update(self, test_db_session, sample_sales_user):
        """Test non-admin cannot update users."""
        target_user = User(
            email="target@test.com",
            username="target",
            hashed_password="hash",
            role=UserRole.ANALYST
        )
        test_db_session.add(target_user)
        test_db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            validate_user_update(
                target_user.id,
                None,
                None,
                sample_sales_user,
                test_db_session
            )
        assert exc_info.value.status_code == 403
    
    def test_cannot_change_own_role(self, test_db_session, sample_admin_user):
        """Test user cannot change own role."""
        with pytest.raises(HTTPException) as exc_info:
            validate_user_update(
                sample_admin_user.id,
                UserRole.SALES_TEAM,
                None,
                sample_admin_user,
                test_db_session
            )
        assert exc_info.value.status_code == 403


class TestGetUserSalesTeamId:
    """Test get user sales team ID."""
    
    def test_sales_team_with_id(self, sample_sales_user, sample_sales_team):
        """Test getting sales team ID for user with assignment."""
        result = get_user_sales_team_id(sample_sales_user)
        assert result == sample_sales_team.id
    
    def test_sales_team_without_id(self, test_db_session):
        """Test getting sales team ID for user without assignment."""
        user = User(
            email="test@test.com",
            username="test",
            hashed_password="hash",
            role=UserRole.SALES_TEAM,
            sales_team_id=None
        )
        test_db_session.add(user)
        test_db_session.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            get_user_sales_team_id(user)
        assert exc_info.value.status_code == 400
    
    def test_admin_returns_none(self, sample_admin_user):
        """Test admin returns None (no sales team)."""
        result = get_user_sales_team_id(sample_admin_user)
        assert result is None

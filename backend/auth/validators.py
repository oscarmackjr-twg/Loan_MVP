"""Validation functions for authentication and authorization."""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from db.models import User, SalesTeam, UserRole


def validate_sales_team_assignment(
    role: UserRole,
    sales_team_id: int | None,
    db: Session
) -> None:
    """
    Validate that SALES_TEAM users have a sales_team_id assigned.
    
    Args:
        role: User role
        sales_team_id: Optional sales team ID
        db: Database session
    
    Raises:
        HTTPException: If validation fails
    """
    if role == UserRole.SALES_TEAM:
        if sales_team_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sales team users must be assigned to a sales team"
            )
        
        # Verify sales team exists and is active
        sales_team = db.query(SalesTeam).filter(
            SalesTeam.id == sales_team_id,
            SalesTeam.is_active == True
        ).first()
        
        if not sales_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sales team with ID {sales_team_id} not found or inactive"
            )


def validate_sales_team_access(
    user: User,
    target_sales_team_id: int | None
) -> None:
    """
    Validate that user can access data for a specific sales team.
    
    Args:
        user: Current user
        target_sales_team_id: Sales team ID of target data
    
    Raises:
        HTTPException: If access is denied
    """
    # Admins can access all data
    if user.role == UserRole.ADMIN:
        return
    
    # Analysts can access all data (for now)
    if user.role == UserRole.ANALYST:
        return
    
    # Sales team users can only access their own team's data
    if user.role == UserRole.SALES_TEAM:
        if user.sales_team_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be assigned to a sales team"
            )
        
        if target_sales_team_id is not None and user.sales_team_id != target_sales_team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access other sales team's data"
            )


def validate_user_update(
    user_id: int,
    role: UserRole | None,
    sales_team_id: int | None,
    current_user: User,
    db: Session
) -> None:
    """
    Validate user update permissions and data.
    
    Args:
        user_id: ID of user being updated
        role: New role (if changing)
        sales_team_id: New sales team ID (if changing)
        current_user: User making the update
        db: Database session
    
    Raises:
        HTTPException: If validation fails
    """
    # Only admins can update users
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users"
        )
    
    # Validate sales team assignment if role is being set/changed
    if role is not None:
        validate_sales_team_assignment(role, sales_team_id, db)
    
    # Users cannot change their own role (security measure)
    if user_id == current_user.id and role is not None and role != current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users cannot change their own role"
        )


def get_user_sales_team_id(user: User) -> int | None:
    """
    Get sales team ID for user, ensuring SALES_TEAM users have one.
    
    Args:
        user: User object
    
    Returns:
        Sales team ID or None
    
    Raises:
        HTTPException: If SALES_TEAM user has no sales_team_id
    """
    if user.role == UserRole.SALES_TEAM:
        if user.sales_team_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sales team user must have sales_team_id assigned"
            )
        return user.sales_team_id
    
    return user.sales_team_id

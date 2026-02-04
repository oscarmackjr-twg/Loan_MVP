"""Audit logging for authentication and authorization."""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from db.models import User

logger = logging.getLogger(__name__)


def log_user_action(
    action: str,
    user: User,
    target_user_id: Optional[int] = None,
    details: Optional[dict] = None
):
    """
    Log user action for audit trail.
    
    Args:
        action: Action performed (e.g., 'login', 'create_user', 'update_user')
        user: User performing the action
        target_user_id: Optional ID of target user (for user management actions)
        details: Optional additional details
    """
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': action,
        'user_id': user.id,
        'username': user.username,
        'user_role': user.role.value,
        'sales_team_id': user.sales_team_id,
    }
    
    if target_user_id:
        log_data['target_user_id'] = target_user_id
    
    if details:
        log_data.update(details)
    
    logger.info(f"User action: {log_data}")


def log_data_access(
    user: User,
    resource_type: str,
    resource_id: Optional[str] = None,
    sales_team_id: Optional[int] = None
):
    """
    Log data access for audit trail.
    
    Args:
        user: User accessing data
        resource_type: Type of resource (e.g., 'pipeline_run', 'loan_fact')
        resource_id: Optional resource ID
        sales_team_id: Optional sales team ID of accessed data
    """
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': 'data_access',
        'user_id': user.id,
        'username': user.username,
        'user_role': user.role.value,
        'user_sales_team_id': user.sales_team_id,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'accessed_sales_team_id': sales_team_id,
    }
    
    logger.info(f"Data access: {log_data}")


def log_authorization_failure(
    user: User,
    action: str,
    reason: str,
    resource_id: Optional[str] = None
):
    """
    Log authorization failure for security monitoring.
    
    Args:
        user: User attempting action
        action: Action attempted
        reason: Reason for failure
        resource_id: Optional resource ID
    """
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'action': 'authorization_failure',
        'user_id': user.id,
        'username': user.username,
        'user_role': user.role.value,
        'sales_team_id': user.sales_team_id,
        'attempted_action': action,
        'reason': reason,
        'resource_id': resource_id,
    }
    
    logger.warning(f"Authorization failure: {log_data}")

"""Notification utilities for scheduler events."""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def send_notification(
    event_type: str,
    sales_team_id: Optional[int],
    message: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Send notification for scheduler events.
    
    This is a placeholder for notification integration (email, Slack, etc.).
    Currently logs to logger, but can be extended to send actual notifications.
    
    Args:
        event_type: Type of event ('run_started', 'run_completed', 'run_failed')
        sales_team_id: Optional sales team ID
        message: Notification message
        details: Optional additional details
    """
    notification_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'sales_team_id': sales_team_id,
        'message': message,
    }
    
    if details:
        notification_data.update(details)
    
    # Log notification (can be extended to send email/Slack/etc.)
    if event_type == 'run_failed':
        logger.error(f"NOTIFICATION: {notification_data}")
    else:
        logger.info(f"NOTIFICATION: {notification_data}")
    
    # TODO: Implement actual notification sending
    # Example:
    # if settings.ENABLE_EMAIL_NOTIFICATIONS:
    #     send_email_notification(notification_data)
    # if settings.SLACK_WEBHOOK_URL:
    #     send_slack_notification(notification_data)


def notify_run_started(sales_team_id: Optional[int], run_id: str):
    """Notify that a pipeline run has started."""
    team_str = f"sales_team_{sales_team_id}" if sales_team_id else "general"
    send_notification(
        'run_started',
        sales_team_id,
        f"Pipeline run started for {team_str}",
        {'run_id': run_id}
    )


def notify_run_completed(sales_team_id: Optional[int], run_id: str, result: Dict[str, Any]):
    """Notify that a pipeline run has completed."""
    team_str = f"sales_team_{sales_team_id}" if sales_team_id else "general"
    send_notification(
        'run_completed',
        sales_team_id,
        f"Pipeline run completed for {team_str}",
        {
            'run_id': run_id,
            'total_loans': result.get('total_loans', 0),
            'total_balance': result.get('total_balance', 0),
            'exceptions_count': result.get('exceptions_count', 0)
        }
    )


def notify_run_failed(sales_team_id: Optional[int], run_id: Optional[str], error: str):
    """Notify that a pipeline run has failed."""
    team_str = f"sales_team_{sales_team_id}" if sales_team_id else "general"
    send_notification(
        'run_failed',
        sales_team_id,
        f"Pipeline run failed for {team_str}",
        {
            'run_id': run_id,
            'error': error
        }
    )
